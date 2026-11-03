"""Checkpoint 1 private operator driver. Never emit command stdout or credentials."""
import datetime,gzip,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
WORK=ROOT/'build/phase-c-checkpoint1-1';OUT=ROOT/'reports/phase-c-checkpoint1-1'
WORK.mkdir(parents=True,exist_ok=True,mode=0o700);WORK.chmod(0o700)
OUT.mkdir(parents=True,exist_ok=True)
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
SITE='cpjudge-b01-site'

def run(name,args,data=None):
 p=subprocess.run(args,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 path=WORK/(STAMP+'-'+name+'.log');path.write_bytes(p.stdout+p.stderr);path.chmod(0o600)
 f=OUT/'commands.json';records=json.loads(f.read_text()) if f.exists() else []
 records.append({'name':name,'argv':args,'exit_status':p.returncode,'private_log':str(path.relative_to(ROOT))})
 f.write_text(json.dumps(records,indent=2)+'\n')
 print(name+': exit '+str(p.returncode),flush=True)
 if p.returncode:raise RuntimeError(name+' failed; inspect private log')
 return p.stdout

def docker(name,*args,data=None):return run(name,['docker',*args],data)
def shell(name,code,settings=None):
 args=['exec','-i',SITE,'python','manage.py','shell']
 if settings:args+=['--settings='+settings]
 return docker(name,*args,data=code.encode())
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')

def smoke_report(raw):
 keep=('status','submission_id','url','selected_language','displayed_verdict','displayed_long_verdict','displayed_case_count','displayed_score','actual_native_form_post_count','page_error_count','source_injected_only_into_native_Ace_form')
 result={k:raw[k] for k in keep}
 result.update(all_cases_AC=all(s=='AC' for s in raw['displayed_cases']),contiguous_case_numbers_verified=raw['displayed_case_numbers']==list(range(1,104)),authenticated_poll_count=len(raw['authenticated_poll_responses']),all_polls_authorized=all(s==200 for s in raw['authenticated_poll_responses']))
 return result

def backup():
 data=docker('private-backup','exec','cpjudge-b01-db','sh','-c',
       'exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
 path=WORK/(STAMP+'-database.sql.gz')
 with path.open('xb') as output:
  os.chmod(path,0o600);output.write(gzip.compress(data))
 assert gzip.decompress(path.read_bytes())==data and b'-- Dump completed on' in data
 # Snapshot application rows separately for precise preservation checks after real activity.
 state=shell('private-row-snapshot',"""import json
from django.apps import apps
from pathlib import Path
from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
rows={m._meta.label_lower:list(m.objects.order_by(m._meta.pk.name).values()) for m in apps.get_models() if not m._meta.proxy}
p=Path('/tmp/c1-before-rows.json');assert not p.exists()
p.write_text(json.dumps(rows,default=str));p.chmod(0o600)
print('Baseline captured privately; no in-progress submissions.')
""")
 docker('copy-private-snapshot','cp',SITE+':/tmp/c1-before-rows.json',str(WORK/'before-rows.json'))
 (WORK/'before-rows.json').chmod(0o600)
 save('backup.json',{'status':'PASS','private_backup':str(path.relative_to(ROOT)),'readback':'gzip full-byte round trip','database_restore':'NOT RUN'})

if __name__=='__main__':
 action=sys.argv[1]
 if action=='exposure':
  prior=json.loads((ROOT/'reports/phase-c-1/backup.json').read_text())
  raw=gzip.decompress((ROOT/prior['private_backup']).read_bytes())
  nonempty=set(m[1].decode() for m in re.finditer(rb'^INSERT INTO `([^`]+)`',raw,re.M))
  categories={
    'account identifiers, names/contact emails and password hashes':'auth_user' in nonempty,
    'profile metadata including access IPs and configured authentication metadata':'judge_profile' in nonempty,
    'active session identifiers and signed/serialized session records':'django_session' in nonempty,
    'worker registration authentication material':'judge_judge' in nonempty,
    'private problem statements/metadata and contest/entrant records':'judge_problem' in nonempty,
    'submitted solution source, results, compiler diagnostics and case metrics':'judge_submission' in nonempty and 'judge_submissionsource' in nonempty,
  }
  save('exposure.json',{'assessment':'The initial command emitted a full SQL dump into tool output; treat its nonempty sensitive tables as potentially exposed. No values reproduced.',
    'categories_present':categories,'plaintext_account_passwords':'Not stored in auth_user; password hashes were in the dump.',
    'environment_secrets':'Database/server SECRET_KEY and DB passwords are not included merely by a database dump; no claim that separate environment files were exposed.',
    'remediation':'Restrict/delete the exposed tool transcript through its owning interface where possible; treat worker registration key and active session records as compromised outside trusted recipients. Invalidate old sessions on activation. Schedule explicit worker-key replacement and account password resets if transcript access was untrusted. No existing credentials silently rotated.'})
  print('Exposure assessed locally; category-only report written.')
 elif action=='stage':
  docker('stage-app','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
  for local,remote in [('native_settings.py','cpj_native_settings.py'),('integration_settings.py','cpj_integration_settings.py')]:
   docker('stage-'+local,'cp',str(HERE/local),SITE+':/app/dmoj/'+remote)
  docker('test-database-grant','exec','cpjudge-b01-db','sh','-c','exec mariadb --user=root --password="$MARIADB_ROOT_PASSWORD" -e "GRANT ALL ON test_cpj_phase_c.* TO b01;"')
  docker('generate-additive-policy-migration','exec','--user','1000:1000',SITE,'python','manage.py','makemigrations','cpjudge','--settings=dmoj.cpj_integration_settings')
  docker('retain-migrations','cp',SITE+':/app/cpjudge/migrations/.',str(HERE/'cpjudge/migrations'))
 elif action=='tests':
  docker('refresh-isolated-integration-settings','cp',str(HERE/'integration_settings.py'),SITE+':/app/dmoj/cpj_integration_settings.py')
  docker('stage-integration-tests','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
  docker('native-integration-tests','exec','--user','1000:1000',SITE,'python','manage.py','test','cpjudge.integration_tests','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='targeted-races':
  docker('stage-final-targeted-tests','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
  docker('correction-and-native-conflict-races','exec','--user','1000:1000',SITE,'python','manage.py','test',
      'cpjudge.integration_tests.NativeRaceTests.test_concurrent_correction_reserves_one_owner_without_merging',
      'cpjudge.integration_tests.NativeIntegrationTests.test_conflict_flag_survives_revocation_and_native_join_is_unranked',
      'cpjudge.integration_tests.NativeIntegrationTests.test_scoped_delegate_admin_and_roster_only_conflict_policy',
      '--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='backup':backup()
 elif action=='activate':
  assert (OUT/'backup.json').exists(), 'Take a fresh private readable backup first'
  assert not (WORK/'enabled').exists(), 'Already activated; inspect state'
  os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
  docker('reload-http','exec','-i',SITE,'python',data=b"import os,signal\nfrom pathlib import Path\nfor p in Path('/proc').iterdir():\n if not p.name.isdigit():continue\n try:a=(p/'cmdline').read_bytes().split(bytes([0]))\n except OSError:continue\n if a[1:3]==[b'manage.py',b'runserver']:os.kill(int(p.name),signal.SIGTERM)\n")
  run('idle-worker-stop',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'stop'])
  run('idle-background-stop',['python3','-B',str(ROOT/'deploy/site-local/b02.py'),'stop'])
  docker('save-prior-settings','cp',SITE+':/app/dmoj/local_settings.py',str(WORK/'local_settings.before.py'))
  (WORK/'local_settings.before.py').chmod(0o600)
  for src,dest in [('resources/event.js','/app/resources/event.js'),('resources/event.js','/app/static/event.js')]:
   docker('install-polling-'+dest.split('/')[-2],'cp',str(HERE/src),SITE+':'+dest)
  shell('enable-native-settings',r"""from pathlib import Path
p=Path('/app/dmoj/local_settings.py');s=p.read_text()
line="exec(open('/app/dmoj/cpj_native_settings.py').read())"
assert line not in s
p.write_text(s+'\n# Phase C checkpoint 1 live policy overlay\n'+line+'\n')
print('Live policy overlay appended; no credentials changed.')
""")
  docker('apply-real-additive-migrations','exec',SITE,'python','manage.py','migrate','--noinput')
  docker('migration-consistency','exec',SITE,'python','manage.py','makemigrations','--check','--dry-run')
  shell('strong-hash-and-native-configuration',"""from django.conf import settings
from django.contrib.auth.hashers import make_password,identify_hasher
assert settings.CPJ_NATIVE and settings.ROOT_URLCONF=='cpjudge.urls'
assert all('MD5' not in h and 'Unsalted' not in h for h in settings.PASSWORD_HASHERS)
assert identify_hasher(make_password('temporary-check-not-an-account')).algorithm=='pbkdf2_sha256'
assert not settings.EVENT_DAEMON_USE
print('Native app enabled with strong PBKDF2 hashing, authenticated polling and real database migrations.')
""")
  # Marker ensures supported B02 start never reopens the unauthenticated daemon.
  (WORK/'enabled').write_text('Checkpoint1 authenticated database polling; native daemon stays stopped.\n')
  docker('start-http','exec','-d',SITE,'sh','-c','exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/c1-http.log 2>&1')
  run('managed-restart-native-services',['python3','-B',str(ROOT/'deploy/site-local/manage.py'),'start'])
  save('activation.json',{'status':'ACTIVATED; live acceptance pending','test_settings_used':False,'hashing':'Django PBKDF2 default work factor','daemon':'stopped; lifecycle prevents restart','rollback':'c1.py rollback; additive schema retained'})
 elif action=='fixture':
  assert (WORK/'enabled').exists()
  shell('create-live-scope-fixture',(HERE/'live_fixture.py').read_text())
  docker('copy-private-live-accounts','cp',SITE+':/tmp/c1-live-accounts.json',str(WORK/'accounts.json'))
  (WORK/'accounts.json').chmod(0o600)
 elif action=='browser':
  docker('live-native-browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
       '--mount',f'type=bind,src={WORK},dst=/results','--mount',f'type=bind,src={HERE/"live_browser.py"},dst=/tests/browser.py,readonly',
       'cpjudge-b01-browser:local1','python','/tests/browser.py')
  save('browser.json',json.loads((WORK/'browser.json').read_text()))
 elif action=='recovery':
  assert not (WORK/'recovery.json').exists(), 'Inspect existing recovery; never blindly reset'
  docker('local-organizer-reset-test-account','exec',SITE,'python','manage.py','college_account','reset','C1LIVEP','--actor','C1LIVEADMIN','--credential-file','/tmp/c1-recovery.json')
  docker('copy-test-only-recovery','cp',SITE+':/tmp/c1-recovery.json',str(WORK/'recovery.json'));(WORK/'recovery.json').chmod(0o600)
  q=json.loads((WORK/'accounts.json').read_text())['accounts']['q']
  docker('audited-test-id-correction','exec',SITE,'python','manage.py','correct_college_id',str(q['id']),'C1LIVECORRECTED','--actor','C1LIVEADMIN','--reason','Task-owned registrar correction acceptance fixture')
  docker('live-recovery-browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
       '--mount',f'type=bind,src={WORK},dst=/results','--mount',f'type=bind,src={HERE/"live_recovery_browser.py"},dst=/tests/browser.py,readonly',
       'cpjudge-b01-browser:local1','python','/tests/browser.py')
  save('recovery-browser.json',json.loads((WORK/'recovery-browser.json').read_text()))
 elif action=='submit':
  assert not (WORK/'submission-receipt.json').exists(), 'Never blindly repeat a real submission'
  source=ROOT/'build/a03-judge-1/pipeline/problems/gaming-grid/solutions/reference.cpp'
  assert source.is_file()
  shell('idle-online-before-smoke',"""from judge.models import Judge,Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
j=Judge.objects.get(name='cpjudge-local-worker');assert j.online and j.problems.filter(code='pv000000000000000001').exists()
assert j.runtimes.filter(key='CPP23').exists()
print('Idle native worker and existing immutable CPP23 problem available.')
""")
  docker('native-browser-judging-smoke','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
       '--mount',f'type=bind,src={WORK},dst=/results','--mount',f'type=bind,src={source},dst=/run/reference.cpp,readonly',
       '--mount',f'type=bind,src={HERE/"live_submission.py"},dst=/tests/browser.py,readonly',
       'cpjudge-b01-browser:local1','python','/tests/browser.py')
  raw=json.loads((WORK/'result.json').read_text())
  save('judging-browser.json',smoke_report(raw))
 elif action=='verify':
  receipt=json.loads((WORK/'smoke-after-fix/submission-receipt.json').read_text());sid=receipt['submission_id']
  # Only sanitized counts and booleans leave this private comparison.
  rotated_key_change=(WORK/'rotation.json').exists()
  data=shell('native-results-and-preservation',"SUBMISSION_ID="+str(sid)+"\nROTATED_KEY_CHANGE="+str(rotated_key_change)+"\n"+"""import json
from pathlib import Path
from django.apps import apps
from django.conf import settings
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth import get_user_model
from judge.models import Submission,Judge
from cpjudge.models import Identity
before=json.loads(Path('/tmp/c1-before-rows.json').read_text())
allowed={'auth.user':{'last_login'},'judge.profile':{'last_access','ip'},'judge.problem':{'user_count','ac_rate'},'judge.judge':{'online','ping','load','start_time','last_ip'}}
if ROTATED_KEY_CHANGE:allowed['judge.judge'].add('auth_key')
changes={}
for name,oldrows in before.items():
 if name in ('judge.runtimeversion','sessions.session'):continue
 model=apps.get_model(name);pk=model._meta.pk.attname
 rows={r[pk]:r for r in json.loads(json.dumps(list(model.objects.all().values()),default=str))}
 for old in oldrows:
  assert old[pk] in rows, 'An existing row disappeared: '+name
  changed={k for k in old if old[k]!=rows[old[pk]][k]}
  assert changed <= allowed.get(name,set()), 'Unexpected existing-row change: '+name+':'+','.join(sorted(changed))
  if changed:changes.setdefault(name,set()).update(changed)
s=Submission.objects.select_related('language','judged_on').get(pk=SUBMISSION_ID)
assert s.status=='D' and s.result=='AC' and s.language.key=='CPP23'
cases=list(s.test_cases.order_by('case').values_list('case','status','points','total'))
assert cases==[(n,'AC',1.0,1.0) for n in range(1,104)]
assert s.case_points==103 and s.case_total==103 and s.judged_on.name=='cpjudge-local-worker'
assert s.contest_object.key=='c1livea'
assert Judge.objects.get(name='cpjudge-local-worker').online
for user in get_user_model().objects.filter(username__startswith='C1LIVE'):
 assert identify_hasher(user.password).algorithm=='pbkdf2_sha256'
assert settings.CPJ_NATIVE and settings.ROOT_URLCONF=='cpjudge.urls'
assert all('MD5' not in h for h in settings.PASSWORD_HASHERS)
assert not settings.EVENT_DAEMON_USE
print('C1_RESULT='+json.dumps({'status':'PASS','old_account_passwords_sources_results_contests_preserved':True,
 'old_models_checked':len(before),'allowed_native_activity':{k:sorted(v) for k,v in changes.items()},
 'new_submission_id':s.pk,'verdict':'AC','actual_AC_cases':103,'native_contest_attached':True,
 'new_accounts_strong_PBKDF2':True,'worker_online':True}))
""")
  result=json.loads(data.decode().split('C1_RESULT=',1)[1])
  import socket
  ports={}
  for port in (9995,9996):
   with socket.socket() as connection:
    connection.settimeout(1);ports[str(port)]=connection.connect_ex(('127.0.0.1',port))!=0
  assert all(ports.values()), 'Unauthenticated daemon port reachable'
  event=json.loads(docker('event-disabled-state','inspect','cpjudge-b02-events'))[0]
  assert not event['State']['Running']
  worker=json.loads(docker('worker-preserved-configuration','inspect','cpjudge-b03-worker'))[0]
  import hashlib
  cfg_hash=hashlib.sha256(json.dumps({k:worker[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()
  baseline=json.loads((ROOT/'reports/b12-restart-1/final-containers.json').read_text())['cpjudge-b03-worker']
  assert worker['Id']==baseline['id'] and worker['Image']==baseline['image'] and cfg_hash==baseline['configuration_sha256']
  from tools.site_problem import file_manifest
  mount=next(m for m in worker['Mounts'] if m['Destination']=='/problems');assert not mount['RW']
  assert file_manifest(Path(mount['Source'])/'pv000000000000000001')==baseline['immutable_files']
  result.update(unprotected_ports_closed=ports,old_event_daemon_stopped=True,worker_container_image_sandbox_and_problem_files_preserved=True)
  # Native passive observer confirms actual request/callback progression.
  trace=docker('private-native-smoke-trace','exec',SITE,'cat','/tmp/b07-native-trace.jsonl')
  records=[json.loads(line) for line in trace.splitlines() if line]
  records=[r for r in records if r.get('submission-id')==sid]
  assert len([r for r in records if r['name']=='submission-request'])==1
  callback_cases=sorted([c for r in records for c in r.get('cases',[])],key=lambda c:c['position'])
  assert len(callback_cases)==103 and [c['position'] for c in callback_cases]==list(range(1,104))
  assert all(c['status']==0 and c['points']==c['total-points']==1 for c in callback_cases)
  assert any(r['name']=='grading-end' for r in records)
  result['native_request_callback_SQL_and_browser_agree']=True
  save('acceptance.json',result)
 elif action=='recover-dispatch':
  # This one task-owned admission failed before any worker execution. Preserve it.
  receipt=json.loads((WORK/'submission-receipt.json').read_text());sid=receipt['submission_id']
  shell('confirm-only-failed-test-admission',"SID="+str(sid)+"\n"+"""from judge.models import Submission
active=list(Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).values_list('pk',flat=True))
assert active==[SID]
s=Submission.objects.get(pk=SID);assert s.user.user.username=='C1LIVEP' and s.status=='QU' and not s.test_cases.exists()
print('Only task-owned pre-dispatch-failure receipt is active; zero executed cases.')
""")
  # Stop only the temporary browser owning this smoke, identified by its source mount.
  ids=docker('find-task-browser','ps','-q','--filter','ancestor=cpjudge-b01-browser:local1').decode().split()
  for cid in ids:
   obj=json.loads(docker('inspect-task-browser','inspect',cid))[0]
   if any(m.get('Source')==str(HERE/'live_submission.py') for m in obj['Mounts']):
    docker('stop-failed-test-browser','stop',cid)
  docker('native-worker-disconnect-after-pre-dispatch-error','stop','--signal','SIGINT','--time','20','cpjudge-b03-worker')
  import time
  for _ in range(20):
   value=shell('observe-native-failure',"from judge.models import Submission\ns=Submission.objects.get(pk="+str(sid)+")\nprint('C1_FAILURE='+s.status+' '+str(s.result))\n")
   if b'C1_FAILURE=IE IE' in value:break
   time.sleep(1)
  else:raise RuntimeError('Native bridge did not record infrastructure failure')
  os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
  run('stop-idle-native-services-after-failure',['python3','-B',str(ROOT/'deploy/site-local/b02.py'),'stop'])
  docker('install-commit-dispatch-fix','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
  docker('reload-http-after-dispatch-fix','exec','-i',SITE,'python',data=b"import os,signal\nfrom pathlib import Path\nfor p in Path('/proc').iterdir():\n if not p.name.isdigit():continue\n try:a=(p/'cmdline').read_bytes().split(bytes([0]))\n except OSError:continue\n if a[1:3]==[b'manage.py',b'runserver']:os.kill(int(p.name),signal.SIGTERM)\n")
  docker('start-http-after-dispatch-fix','exec','-d',SITE,'sh','-c','exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/c1-http-after-fix.log 2>&1')
  run('managed-reconnect-after-dispatch-fix',['python3','-B',str(ROOT/'deploy/site-local/manage.py'),'start'])
  save('dispatch-failure.json',{'submission_id':sid,'status':'Native IE after worker disconnect; zero cases executed',
      'cause':'Session generation transaction delayed visibility of new native row until after early dispatch',
      'fix':'Dispatch on outer transaction commit; rolled-back admissions never dispatch','fresh_smoke':'pending'})
 elif action=='submit-after-fix':
  import shutil
  smoke=WORK/'smoke-after-fix';smoke.mkdir(mode=0o700,exist_ok=True)
  assert not (smoke/'submission-receipt.json').exists(), 'Inspect receipt; do not repeat a POST'
  shell('fresh-smoke-admission-guard',"from judge.models import Submission\nqs=Submission.objects.filter(user__user__username='C1LIVEP')\nassert qs.count()==1 and qs.get().status=='IE' and not qs.get().test_cases.exists()\nprint('Only the retained IE test receipt exists; fresh submission is authorized.')\n")
  shutil.copy2(WORK/'accounts.json',smoke/'accounts.json')
  source=ROOT/'build/a03-judge-1/pipeline/problems/gaming-grid/solutions/reference.cpp'
  docker('fresh-native-browser-smoke-after-fix','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
       '--mount',f'type=bind,src={smoke},dst=/results','--mount',f'type=bind,src={source},dst=/run/reference.cpp,readonly',
       '--mount',f'type=bind,src={HERE/"live_submission.py"},dst=/tests/browser.py,readonly',
       'cpjudge-b01-browser:local1','python','/tests/browser.py')
  raw=json.loads((smoke/'result.json').read_text())
  save('judging-browser.json',smoke_report(raw))
 elif action=='refresh-web':
  shell('idle-before-final-web-refresh',"from judge.models import Submission\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\n")
  docker('copy-final-native-app','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
  docker('stop-http-for-final-app','exec','-i',SITE,'python',data=b"import os,signal\nfrom pathlib import Path\nfor p in Path('/proc').iterdir():\n if not p.name.isdigit():continue\n try:a=(p/'cmdline').read_bytes().split(bytes([0]))\n except OSError:continue\n if a[1:3]==[b'manage.py',b'runserver']:os.kill(int(p.name),signal.SIGTERM)\n")
  docker('start-http-final-app','exec','-d',SITE,'sh','-c','exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/c1-http-final.log 2>&1')
 elif action=='legacy-browser':
  docker('legacy-credential-browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
       '--mount',f'type=bind,src={WORK},dst=/results','--mount',f'type=bind,src={ROOT/"build/b01-site-1/private/accounts.json"},dst=/run/legacy.json,readonly',
       '--mount',f'type=bind,src={HERE/"legacy_browser.py"},dst=/tests/browser.py,readonly',
       'cpjudge-b01-browser:local1','python','/tests/browser.py')
  save('legacy-browser.json',json.loads((WORK/'legacy-browser.json').read_text()))
 elif action=='stale-export-job':
  data=shell('queue-deliberately-stale-export',"""import secrets,json
from django.contrib.auth import get_user_model
from judge.models import Contest
from cpjudge.models import Identity,ExportJob
from cpjudge.tasks import export_roster
u=get_user_model().objects.get(username='C1LIVEA');i=Identity.objects.get(user=u)
j=ExportJob.objects.create(owner=u,contest=Contest.objects.get(key='c1livea'),generation=i.generation-1,token=secrets.token_hex(24))
export_roster.delay(j.pk)
print('C1_JOB='+str(j.pk))
""")
  job=int(data.decode().split('C1_JOB=',1)[1].split()[0])
  import time
  for _ in range(20):
   value=shell('check-worker-stale-export-denial',"from cpjudge.models import ExportJob\nprint('C1_STATUS='+ExportJob.objects.get(pk="+str(job)+").status)\n")
   if b'C1_STATUS=denied' in value:break
   time.sleep(1)
  else:raise RuntimeError('Stale background export was not denied')
  save('stale-export-job.json',{'status':'PASS','test':'Deliberately stale-generation export sent through real Celery and denied at execution','participant_emails_exported':False})
 elif action=='final-access':
  sid=json.loads((WORK/'smoke-after-fix/submission-receipt.json').read_text())['submission_id']
  data=shell('private-smoke-channel-fixture',"import json\nfrom judge.models import Submission\ns=Submission.objects.get(pk="+str(sid)+")\nprint('C1_PRIVATE='+json.dumps({'id':s.pk,'secret':s.id_secret}))\n")
  path=WORK/'private-smoke.json';path.write_text(data.decode().split('C1_PRIVATE=',1)[1]);path.chmod(0o600)
  docker('final-live-access-browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
       '--mount',f'type=bind,src={WORK},dst=/results','--mount',f'type=bind,src={HERE/"final_access_browser.py"},dst=/tests/browser.py,readonly',
       'cpjudge-b01-browser:local1','python','/tests/browser.py')
  save('final-access-browser.json',json.loads((WORK/'final-access-browser.json').read_text()))
 elif action=='lifecycle-check':
  os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
  run('supported-start-retains-secure-configuration',['python3','-B',str(ROOT/'deploy/site-local/manage.py'),'start'])
 elif action=='retire-test-admin':
  shell('disable-only-task-owned-elevated-account',"""from django.contrib.auth import get_user_model
from django.db import transaction
from cpjudge.models import Identity,Audit
U=get_user_model()
with transaction.atomic():
 u=U.objects.select_for_update().get(username='C1LIVEADMIN')
 assert Audit.objects.filter(subject=u,action='fixture.admin').exists()
 actor=U.objects.filter(is_superuser=True,is_active=True).exclude(pk=u.pk).order_by('pk').first()
 u.is_active=False;u.save(update_fields=['is_active'])
 i=Identity.objects.get(user=u);i.generation+=1;i.save(update_fields=['generation'])
 Audit.objects.create(actor=actor,subject=u,action='fixture.disable')
print('Temporary elevated acceptance account disabled and its sessions revoked; history/password retained.')
""")
  save('fixture-cleanup.json',{'temporary_elevated_test_account':'disabled; generation revoked','other_task_fixtures':'private c1livea/b, ordinary/scoped-author accounts and native attempts retained for review','existing_accounts_changed':False})
 elif action=='rotate-exposure':
  # Rotate only the B03 transport credential and invalidate server-side sessions.
  # Secret-bearing data stays in memory, stdin, or ignored mode-0600 files.
  import secrets, tempfile, time
  assert (WORK/'enabled').exists()
  credential=ROOT/'build/b03-worker-1/private/worker.json'
  config=ROOT/'build/b03-worker-1/private/config.yml'
  info=json.loads(credential.read_text());old=info['key']
  assert info['id']=='cpjudge-local-worker' and len(old)>=32
  key_cfg=config.read_text()
  assert key_cfg.count('key: '+json.dumps(old))==1
  assert not (WORK/'rotation.json').exists(), 'Inspect existing remediation receipt; do not rotate twice'
  # Fresh full private DB backup before changing native authentication/session rows.
  dump=docker('rotation-private-db-backup','exec','cpjudge-b01-db','sh','-c',
      'exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
  backup_path=WORK/(STAMP+'-pre-exposure-remediation.sql.gz')
  with backup_path.open('xb') as f:
   os.chmod(backup_path,0o600);f.write(gzip.compress(dump))
  assert gzip.decompress(backup_path.read_bytes())==dump and b'-- Dump completed on' in dump
  # Capture a genuinely authenticated cookie to test server-side invalidation.
  legacy=ROOT/'build/b01-site-1/private/accounts.json'
  docker('capture-pre-revocation-browser-session','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--env','MODE=capture',
       '--mount',f'type=bind,src={WORK},dst=/results','--mount',f'type=bind,src={legacy},dst=/run/legacy.json,readonly',
       '--mount',f'type=bind,src={HERE/"exposure_session_browser.py"},dst=/tests/browser.py,readonly','cpjudge-b01-browser:local1','python','/tests/browser.py','capture')
  # Drain only the owned worker; guard refuses any in-progress judging.
  os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
  run('stop-owned-worker-for-key-rotation',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'stop'])
  shell('assert-worker-offline-before-rotation',"from judge.models import Judge,Submission\nj=Judge.objects.get(name='cpjudge-local-worker');assert not j.online\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nprint('Owned worker offline and no active judging.')")
  new=secrets.token_urlsafe(48);info['key']=new
  # Preserve the pinned runtime block and all sandbox/configuration fields.
  new_config=re.sub(r'(?m)^key: .*$', 'key: '+json.dumps(new), key_cfg)
  assert new_config!=key_cfg and new_config.count('key: '+json.dumps(new))==1
  def atomic_secret(path,data):
   fd,tmp=tempfile.mkstemp(prefix='.rotate-',dir=path.parent)
   try:
    os.fchmod(fd,0o600)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path);os.chmod(path,0o600)
   except BaseException:
    try:os.unlink(tmp)
    except FileNotFoundError:pass
    raise
  # Private proof config is created only for the old-key rejection handshake.
  old_config=WORK/'old-key-probe.yml'
  atomic_secret(old_config,re.sub(r'(?m)^key: .*$', 'key: '+json.dumps(old), key_cfg).encode())
  atomic_secret(credential,json.dumps(info).encode())
  atomic_secret(config,new_config.encode())
  # Send new registration directly over stdin; never place it in argv/log output.
  docker('install-new-private-bridge-registration','exec','-i',SITE,'python','-c',
       "import os,sys;from pathlib import Path;p=Path('/tmp/b03-registration.json');data=sys.stdin.buffer.read();fd=os.open(str(p)+'.rotate',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(fd,data);os.fsync(fd);os.close(fd);os.replace(str(p)+'.rotate',p)",data=json.dumps(info).encode())
  # Atomic DB key replacement and invalidate every stored session and generation.
  code="""import json
from pathlib import Path
from django.db import transaction
from django.contrib.sessions.models import Session
from judge.models import Judge,Submission
from cpjudge.models import Identity
data=json.loads(Path('/tmp/b03-registration.json').read_text())
with transaction.atomic():
 assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
 j=Judge.objects.select_for_update().get(name=data['id']);assert j.auth_key!=data['key']
 j.auth_key=data['key'];j.save(update_fields=['auth_key'])
 for identity in Identity.objects.select_for_update().all().order_by('user_id'):
  identity.generation+=1;identity.save(update_fields=['generation'])
 removed,_=Session.objects.all().delete()
print('ROTATION_RESULT='+json.dumps({'key_changed':True,'identities_revoked':Identity.objects.count(),'session_rows_removed':removed}))
"""
  out=docker('rotate-native-key-and-revoke-sessions','exec','-i',SITE,'python','manage.py','shell',data=code.encode())
  try: summary=json.loads(out.decode().split('ROTATION_RESULT=',1)[1].splitlines()[0])
  except Exception as e:raise RuntimeError('Could not verify sanitized rotation receipt') from e
  # Assert the non-secret identity/config values and PBKDF2 account hashes remain untouched.
  shell('verify-new-registration-without-reading-key',"from judge.models import Judge\nfrom django.contrib.auth.models import User\nfrom django.contrib.auth.hashers import identify_hasher\nj=Judge.objects.get(name='cpjudge-local-worker');assert not j.online\nassert User.objects.exclude(password__startswith='pbkdf2_sha256$').count()==0\nprint('Database registration changed; all account hashes remain PBKDF2.')")
  # Real pinned worker with the old credential must be rejected by the bridge.
  probe='cpjudge-old-key-probe'
  image='sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8'
  bridge_before=docker('snapshot-bridge-auth-log','exec',SITE,'cat','/tmp/b02-bridge.log')
  old_args=['run','--name',probe,'--label','cpjudge.task=PhaseC-old-key-probe','--network','container:'+SITE,'--read-only','--cap-drop','ALL','--cap-add','SYS_PTRACE','--security-opt','no-new-privileges','--pids-limit','128','--memory','2g','--cpus','2','--tmpfs','/tmp:rw,exec,nosuid,size=1g,mode=1777','--env','DMOJ_IN_DOCKER=','--mount',f'type=bind,src={old_config},dst=/config.yml,readonly','--mount',f'type=bind,src={ROOT/"build/b03-worker-1/problems"},dst=/problems,readonly','--entrypoint','/bin/bash',image,'-c','. ~judge/.profile; export HOME=/tmp; exec /env/bin/dmoj -c /config.yml --no-ansi --only-executors CPP11,CPP14,CPP17,CPP20,CPP23 127.0.0.1']
  p=subprocess.Popen(['docker',*old_args],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:time.sleep(5)
  finally:
   subprocess.run(['docker','rm','-f',probe],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   p.wait(timeout=15)
  rejection_log=docker('observe-old-key-rejection','exec',SITE,'cat','/tmp/b02-bridge.log')
  appended=rejection_log[len(bridge_before):]
  assert b'Judge authentication failure:' in appended and b'judge failed authentication' in appended,'Native bridge did not record rejection of the old worker credential'
  # Start only the existing worker; its bind-mounted config now holds the new key.
  run('start-worker-with-new-key',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'start'])
  state=shell('verify-worker-reconnected-with-new-key',"from judge.models import Judge\nj=Judge.objects.get(name='cpjudge-local-worker')\nassert j.online and list(j.runtimes.order_by('key').values_list('key',flat=True))==['CPP11','CPP14','CPP17','CPP20','CPP23']\nprint('New-key native worker is online with all five prior runtimes.')")
  # Check a known old browser cookie now returns to login and existing credential still signs in.
  docker('verify-revoked-session-and-existing-password-browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--env','MODE=verify',
       '--mount',f'type=bind,src={WORK},dst=/results','--mount',f'type=bind,src={legacy},dst=/run/legacy.json,readonly',
       '--mount',f'type=bind,src={HERE/"exposure_session_browser.py"},dst=/tests/browser.py,readonly','cpjudge-b01-browser:local1','python','/tests/browser.py','verify')
  # Remove the test-only old-key copy; no stale local registration is retained.
  old_config.unlink()
  (WORK/'rotation.json').write_text(json.dumps({'status':'PASS','old_worker_key_rejected':True,'new_worker_key_authenticated':True,
       'worker_reconnected':True,'session_rows_removed':summary['session_rows_removed'],'identity_generations_revoked':summary['identities_revoked'],
       'legacy_password_browser':'PASS','fresh_backup':str(backup_path.relative_to(ROOT)),'sandbox_configuration_changed':False})+'\n')
  (WORK/'rotation.json').chmod(0o600)
  save('exposure-remediation.json',json.loads((WORK/'rotation.json').read_text()))
  print('Worker key rotated; exposed sessions invalidated; authentication checks passed.')
 elif action=='verify-rotation-submit':
  import shutil
  receipt=json.loads((WORK/'rotation.json').read_text());assert receipt['status']=='PASS'
  target=WORK/'post-rotation-submit';target.mkdir(mode=0o700,exist_ok=True);target.chmod(0o700)
  account_file=WORK/'accounts.json';source=ROOT/'build/a03-judge-1/pipeline/problems/gaming-grid/solutions/reference.cpp'
  assert account_file.is_file() and source.is_file()
  shutil.copyfile(account_file,target/'accounts.json');(target/'accounts.json').chmod(0o600)
  docker('post-rotation-real-browser-submission','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
       '--mount',f'type=bind,src={target},dst=/results','--mount',f'type=bind,src={source},dst=/run/reference.cpp,readonly',
       '--mount',f'type=bind,src={HERE/"live_submission.py"},dst=/tests/browser.py,readonly',
       'cpjudge-b01-browser:local1','python','/tests/browser.py')
  raw=json.loads((target/'result.json').read_text());summary=smoke_report(raw)
  assert summary['status']=='PASS' and summary['displayed_verdict']=='AC' and summary['displayed_case_count']==103
  assert summary['actual_native_form_post_count']==1 and summary['all_polls_authorized']
  save('exposure-remediation-submission.json',summary)
  print('Post-rotation participant browser submission reached verdict AC on all 103 cases.')
 elif action=='verify-rotation-config':
  info=json.loads((ROOT/'build/b03-worker-1/private/worker.json').read_text())
  config=(ROOT/'build/b03-worker-1/private/config.yml').read_text()
  assert config.count('key: '+json.dumps(info['key']))==1
  shell('verify-bridge-database-worker-key-consistency',"import json\nfrom pathlib import Path\nfrom judge.models import Judge\nr=json.loads(Path('/tmp/b03-registration.json').read_text());j=Judge.objects.get(name='cpjudge-local-worker')\nassert r['id']==j.name and r['key']==j.auth_key and j.online\nprint('Private bridge registration, native database credential and online worker identity agree.')")
  save('exposure-key-consistency.json',{'status':'PASS','host_worker_credential_matches_mounted_config':True,'bridge_registration_matches_database':True,'worker_online':True})
  print('Worker key files and active bridge registration agree; secret values suppressed.')
 elif action=='rollback':
  # Fail closed: stop web/background/worker before removing the policy overlay.
  # Never restore the old DB over results or reopen unprotected event ports.
  assert (WORK/'local_settings.before.py').exists()
  os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
  run('rollback-stop',['python3','-B',str(ROOT/'deploy/site-local/manage.py'),'stop'])
  docker('rollback-start-site-shell','start',SITE)
  docker('rollback-restore-settings','exec','-i',SITE,'python','-c',"import sys;from pathlib import Path;Path('/app/dmoj/local_settings.py').write_bytes(sys.stdin.buffer.read())",data=(WORK/'local_settings.before.py').read_bytes())
  docker('rollback-leave-site-stopped','stop',SITE)
  save('rollback.json',{'status':'Restored prior settings with services stopped; database/rows/additive schema retained.',
    'daemon_ports':'Remain stopped; do not remove enabled marker/reopen ports without a secure replacement.',
    'next':'Review incident; repair and reactivate checkpoint1 before exposing website.'})
 else:raise SystemExit('Unknown action')
