"""C05 single-ZIP live integration; command output stays private and bounded."""
import datetime, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
WORK=ROOT/'build/phase-c-c05-1'
OUT=ROOT/'reports/phase-c-c05-1'
SITE='cpjudge-b01-site'
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
WORK.mkdir(parents=True,exist_ok=True,mode=0o700);WORK.chmod(0o700)
OUT.mkdir(parents=True,exist_ok=True)

def run(name,argv,data=None):
 p=subprocess.run(argv,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 path=WORK/(STAMP+'-'+name+'.log');path.write_bytes(p.stdout);path.chmod(0o600)
 records=json.loads((OUT/'commands.json').read_text()) if (OUT/'commands.json').exists() else []
 records.append({'name':name,'argv':argv,'exit_status':p.returncode,'private_log':str(path.relative_to(ROOT))})
 (OUT/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name+': exit '+str(p.returncode),flush=True)
 if p.returncode:raise RuntimeError(name+' failed; inspect private log')
 return p.stdout

def docker(name,*args,data=None):return run(name,['docker',*args],data)

def shell(name,code):
 return docker(name,'exec','-i',SITE,'python','manage.py','shell',data=code.encode())

if __name__=='__main__':
 action=sys.argv[1]
 if action=='stage':
  docker('stage-native-cpjudge-app','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
  docker('stage-native-settings','cp',str(HERE/'native_settings.py'),SITE+':/app/dmoj/cpj_native_settings.py')
  docker('stage-bounded-archive-preflight','cp',str(ROOT/'compat/archive.py'),SITE+':/app/compat/archive.py')
  docker('stage-integration-tests','cp',str(HERE/'cpjudge/integration_tests.py'),SITE+':/app/cpjudge/integration_tests.py')
  print('C05 code staged; no database schema changed.')
 elif action=='tests':
  docker('focused-c05-native-http-tests','exec','--user','1000:1000',SITE,'python','manage.py','test',
       'cpjudge.integration_tests.NativeUploadHTTPTests','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='grant-fixture':
  shell('grant-task-fixture-import-scope',"""from django.contrib.auth import get_user_model
from judge.models import Contest
from cpjudge.policy import grant_scope
from cpjudge.models import Grant
U=get_user_model();actor=U.objects.filter(is_active=True,is_superuser=True).exclude(username='C1LIVEADMIN').order_by('pk').first()
author=U.objects.get(username='C1LIVEA');contest=Contest.objects.get(key='c1livea')
assert actor and author.is_active
grant_scope(actor,author,contest,'problems.import')
assert Grant.objects.filter(contest=contest,user=author,capability='problems.import',revoked=False).exists()
print('Existing task-owned C1LIVEA fixture has the explicit scoped import capability.')
""")
  (WORK/'fixture.json').write_text(json.dumps({'account':'C1LIVEA','contest':'c1livea','capability':'problems.import'})+'\n')
  (WORK/'fixture.json').chmod(0o600)
  print('Task-owned author fixture scope is prepared.')
 elif action=='restart-web':
  shell('assert-idle-before-http-restart',"from judge.models import Submission\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nprint('No in-progress judging; only the HTTP process will restart.')")
  docker('stop-only-site-http-process','exec','-i',SITE,'python','-c',
       "import os,signal\nfrom pathlib import Path\nfound=[]\nfor p in Path('/proc').iterdir():\n if not p.name.isdigit():continue\n try:a=(p/'cmdline').read_bytes().split(bytes([0]))\n except OSError:continue\n if a[1:3]==[b'manage.py',b'runserver']:\n  found.append(int(p.name));os.kill(int(p.name),signal.SIGTERM)\nassert found\nprint('Stopped only the existing local HTTP server process.')")
  docker('start-only-site-http-process','exec','-d',SITE,'sh','-c','exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/c05-http.log 2>&1')
  for _ in range(30):
   try:
    with urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/',timeout=2) as response:
     if response.status==200:break
   except Exception:time.sleep(1)
  else:raise RuntimeError('Local HTTP site did not return login page')
  print('Site HTTP process restarted; bridge, Celery and worker were not restarted.')
 elif action=='browser':
  credentials=ROOT/'build/phase-c-checkpoint1-1/accounts.json'
  result=WORK/'browser';result.mkdir(exist_ok=True,mode=0o700);result.chmod(0o700)
  docker('actual-c05-browser-and-http-flows','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
       '--mount',f'type=bind,src={result},dst=/results','--mount',f'type=bind,src={credentials},dst=/run/accounts.json,readonly',
       '--mount',f'type=bind,src={HERE/"c05_browser.py"},dst=/tests/c05_browser.py,readonly',
       'cpjudge-b01-browser:local1','python','/tests/c05_browser.py')
  report=json.loads((result/'browser.json').read_text())
  (OUT/'browser.json').write_text(json.dumps(report,indent=2)+'\n')
 elif action=='verify':
  report=json.loads((OUT/'browser.json').read_text())
  job_id=report['accepted_job_id']
  data=shell('verify-c05-private-record-and-file',"JOB_ID="+str(job_id)+"\n"+"""import json,os
from pathlib import Path
from django.conf import settings
from cpjudge.models import ImportJob
from cpjudge.imports import private_root
job=ImportJob.objects.get(pk=JOB_ID)
root=private_root();path=(root/job.archive_key).resolve()
assert job.owner.username=='C1LIVEA' and job.contest.key=='c1livea'
assert job.status=='uploaded' and job.attempt==0 and not job.findings and not job.error
assert ImportJob.objects.filter(owner=job.owner).count()==1
stored=list(root.glob('*.zip'));assert stored==[root/job.archive_key]
assert root.stat().st_mode & 0o777==0o700
assert path.parent==root and path.is_file() and path.stat().st_mode & 0o777==0o600
assert all(not path.is_relative_to(Path(public).resolve()) for public in (settings.MEDIA_ROOT,settings.STATIC_ROOT) if public)
print('C05_STORAGE='+json.dumps({'acceptance':'PASS','job_id':job.pk,'directory_mode':'0700','file_mode':'0600','owner_scoped':True,'single_record_no_failed_request_artifacts':True,'under_public_roots':False,'import_status':job.status,'attempt':job.attempt}))
""")
  item=json.loads(data.decode().split('C05_STORAGE=',1)[1].splitlines()[0])
  (OUT/'storage.json').write_text(json.dumps(item,indent=2)+'\n')
  print('C05 private file and owner-associated upload record verified.')
 else:raise SystemExit('Unknown C05 action')
