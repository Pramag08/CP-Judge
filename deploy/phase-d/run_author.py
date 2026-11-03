"""Sequential D13 local operations; raw output stays private."""
import sys,os,json,gzip,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'deploy/phase-c'))
import c05 as d
HERE=ROOT/'deploy/phase-c';WORK=ROOT/'build/phase-d-d13-1';OUT=ROOT/'reports/phase-d-d13-1'
WORK.mkdir(parents=True,exist_ok=True,mode=0o700);OUT.mkdir(parents=True,exist_ok=True)
d.WORK,d.OUT=WORK,OUT

def shell(file):return d.shell(file,(ROOT/'deploy/phase-d'/f'{file}.py').read_text())
if __name__=='__main__':
 action=sys.argv[1]
 if action=='backup':
  assert not (WORK/'database.sql.gz').exists()
  raw=d.docker('private-full-backup','exec','cpjudge-b01-db','sh','-c','exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
  path=WORK/'database.sql.gz';path.write_bytes(gzip.compress(raw));path.chmod(0o600)
  assert gzip.decompress(path.read_bytes())==raw and b'-- Dump completed on' in raw
  d.shell('private-all-model-snapshot', '''import json
from pathlib import Path
from django.apps import apps
from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
p=Path('/tmp/d13-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('Private snapshot saved; no pending judging.')
''')
 elif action=='stage':d.docker('stage-d13-app','cp',str(HERE/'cpjudge')+'/.',d.SITE+':/app/cpjudge')
 elif action=='migrate':
  assert (WORK/'database.sql.gz').exists()
  d.docker('generate-additive-d13-migration','exec','--user','1000:1000',d.SITE,'python','manage.py','makemigrations','cpjudge','--noinput')
  d.docker('retain-d13-migration','cp',d.SITE+':/app/cpjudge/migrations/.',str(HERE/'cpjudge/migrations'))
  d.docker('apply-additive-d13-migration','exec',d.SITE,'python','manage.py','migrate','--noinput')
 elif action=='regressions':
  d.docker('relevant-author-and-session-regressions','exec','--user','1000:1000',d.SITE,'python','manage.py','test','cpjudge.entry_tests.EntryTests','cpjudge.d01_tests.WorkflowTests.test_server_start_end_inclusive_exclusive_and_receipt','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='tests':d.docker('focused-d13-tests','exec','--user','1000:1000',d.SITE,'python','manage.py','test','cpjudge.author_test_tests.AuthorTests','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='reload':
  import c13_bundle
  d.WORK,d.OUT=WORK,OUT;c13_bundle.reload()
 elif action=='bridge':
  import c11,time
  d.shell('idle-guard-for-readiness-reload','from judge.models import Submission\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()')
  d.run('stop-idle-worker',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'stop'])
  d.docker('stop-idle-bridge','exec','-i',d.SITE,'python','-c',c11.BRIDGE_STOP)
  d.docker('start-bridge-with-publication-check','exec','-d',d.SITE,'sh','-c','exec python manage.py runbridged >> /tmp/b02-bridge.log 2>&1')
  time.sleep(2)
  d.run('start-same-worker',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'start'])
 elif action=='shell':shell(sys.argv[2])
 elif action=='browser':
  folder=WORK/'browser';folder.mkdir(exist_ok=True,mode=0o700)
  d.docker('chromium-d13','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges','--mount',f'type=bind,src={folder},dst=/results','--mount',f'type=bind,src={ROOT/"deploy/phase-d/author_browser.py"},dst=/tests/browser.py,readonly','cpjudge-b01-browser:local1','python','/tests/browser.py')
  shutil.copyfile(folder/'result.json',OUT/'browser.json')
 elif action=='credentials':
  folder=WORK/'browser';folder.mkdir(exist_ok=True,mode=0o700)
  # Reuse existing fixture passwords; look up their current canonical email privately.
  d.docker('copy-private-browser-fixture','cp',d.SITE+':/tmp/d13-browser.json',str(folder/'fixture.json'))
  accounts=json.loads((ROOT/'build/phase-c-checkpoint1-1/accounts.json').read_text())
  data=json.loads((folder/'fixture.json').read_text())
  def visit(v):
   if isinstance(v,dict):
    if 'username' in v and 'password' in v:
     for row in data['accounts']:
      if row['username']==v['username']:row['password']=v['password']
    for x in v.values():visit(x)
   if isinstance(v,list):
    for x in v:visit(x)
  visit(accounts)
  visit(json.loads((ROOT/'build/b01-site-1/private/accounts.json').read_text()))
  visit(json.loads((ROOT/'build/b10-b11-contest-1/accounts.json').read_text()))
  assert all('password' in row for row in data['accounts'])
  (folder/'fixture.json').write_text(json.dumps(data));(folder/'fixture.json').chmod(0o600)
 elif action=='preserve':
  shell('author_preserve')
  d.docker('retain-sanitized-d13-preservation','cp',d.SITE+':/tmp/d13-preservation.json',str(OUT/'preservation.json'))
  # Compare security settings with the retained native C11 container baseline.
  prior=json.loads((ROOT/'build/phase-c-c11-1/containers-before.json').read_text())
  actual=json.loads(d.docker('inspect-same-isolated-worker','inspect','cpjudge-b03-worker'))[0]
  old=prior['cpjudge-b03-worker']
  for key in ('Image','Path','Args'):assert actual[key]==old[key],key
  keys=('CapAdd','CapDrop','SecurityOpt','ReadonlyRootfs','NetworkMode','Memory','NanoCpus','PidsLimit','Tmpfs')
  for key in keys:assert actual['HostConfig'][key]==old['HostConfig'][key],key
  import hashlib
  files=json.loads((ROOT/'build/phase-c-c11-1/files-before.json').read_text())
  for path in ('build/b03-worker-1/private/worker.json','build/b03-worker-1/private/config.yml'):
   file=ROOT/path;assert hashlib.sha256(file.read_bytes()).hexdigest()==files[str(file)]
  (OUT/'checks.json').write_text(json.dumps({'status':'PASS','worker_image_command_and_sandbox_match_retained_c11_baseline':True,'worker_configuration_bytes_match_retained_c11_baseline':True,'security_fields':list(keys)},indent=2)+'\n')
 elif action=='check':
  d.docker('migration-consistency','exec',d.SITE,'python','manage.py','makemigrations','--check','--dry-run')
  d.run('whitespace',['git','diff','--check'])
 else:raise SystemExit('Unknown action')
