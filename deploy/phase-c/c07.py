"""C07 validation driver. Private credentials, subprocess output and files stay ignored."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
import c05 as driver
ROOT=driver.ROOT;HERE=driver.HERE;SITE=driver.SITE
WORK=ROOT/'build/phase-c-c07-1';OUT=ROOT/'reports/phase-c-c07-1'
WORK.mkdir(parents=True,exist_ok=True,mode=0o700);WORK.chmod(0o700);OUT.mkdir(parents=True,exist_ok=True)
driver.WORK=WORK;driver.OUT=OUT

def browser(mode):
 folder=WORK/'browser';folder.mkdir(mode=0o700,exist_ok=True);folder.chmod(0o700)
 package=WORK/'package.zip'
 if not package.exists():driver.docker('copy-existing-synthetic-package','cp',SITE+':/tmp/cpj-tokens.zip',str(package));package.chmod(0o600)
 driver.docker('browser-conversion-'+mode,'run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges','--env','MODE='+mode,
  '--mount',f'type=bind,src={folder},dst=/results','--mount',f'type=bind,src={ROOT/"build/phase-c-checkpoint1-1/accounts.json"},dst=/run/accounts.json,readonly',
  '--mount',f'type=bind,src={package},dst=/run/package.zip,readonly','--mount',f'type=bind,src={HERE/"c07_browser.py"},dst=/tests/browser.py,readonly',
  'cpjudge-b01-browser:local1','python','/tests/browser.py')
 result=json.loads((folder/('browser-'+mode+'.json')).read_text());(OUT/('browser-'+mode+'.json')).write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
 action=sys.argv[1]
 if action=='snapshot':
  data={}
  for name in ('cpjudge-b01-site','cpjudge-b03-worker','cpjudge-b01-db','cpjudge-b01-redis'):
   obj=json.loads(driver.docker('private-container-snapshot-'+name,'inspect',name))[0]
   data[name]={'id':obj['Id'],'image':obj['Image'],'started':obj['State']['StartedAt'],'config_hash':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()}
  (OUT/'containers-before.json').write_text(json.dumps(data,indent=2)+'\n')
 elif action=='tests':
  driver.docker('stage-focused-c07-tests','cp',str(HERE/'cpjudge/c07_tests.py'),SITE+':/app/cpjudge/c07_tests.py')
  driver.docker('stage-c07-resource-tests','cp',str(HERE/'cpjudge/c07_resource_tests.py'),SITE+':/app/cpjudge/c07_resource_tests.py')
  driver.docker('focused-c07-native-tests','exec','--user','1000:1000',SITE,'python','manage.py','test','cpjudge.c07_tests.ConversionTests','cpjudge.c07_tests.ConversionRaceTests','cpjudge.c07_resource_tests.ChildLimitsTests','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='verify-containers':
  before=json.loads((OUT/'containers-before.json').read_text())
  for name,baseline in before.items():
   obj=json.loads(driver.docker('private-final-container-check-'+name,'inspect',name))[0]
   current={'id':obj['Id'],'image':obj['Image'],'started':obj['State']['StartedAt'],'config_hash':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()}
   assert current==baseline,'Unexpected container/sandbox change: '+name
  (OUT/'containers-preserved.json').write_text(json.dumps({'status':'PASS','container_id_image_configuration_and_start_times_unchanged':True,'names':list(before)},indent=2)+'\n')
 elif action=='browser':browser(sys.argv[2] if len(sys.argv)>2 else 'supported')
 elif action=='duplicates':
  source=sys.argv[2] if len(sys.argv)>2 else 'supported'
  sid=json.loads((OUT/('browser-'+source+'.json')).read_text())['job_id']
  code='SID='+str(sid)+'\n'+'''import json,hashlib
from pathlib import Path
from cpjudge.models import ImportJob
from cpjudge.conversion import attempt_path
from cpjudge.tasks import convert_upload
j=ImportJob.objects.get(pk=SID);assert j.status=='succeeded'
before=list(ImportJob.objects.filter(pk=j.pk).values())[0]
root=attempt_path(j.token)
def manifest():return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
original=manifest()
results=[convert_upload.apply_async(args=(j.pk,j.attempt,j.token),queue='cpj_import',retry=False) for _ in range(2)]
assert all(result.get(timeout=30) is False for result in results)
assert list(ImportJob.objects.filter(pk=j.pk).values())[0]==before
assert manifest()==original
print('C07_DUPLICATES='+json.dumps({'status':'PASS','real_Celery_duplicate_deliveries':2,'record_and_output_unchanged':True}))
'''
  raw=driver.shell('real-celery-duplicate-deliveries',code);result=json.loads(raw.decode().split('C07_DUPLICATES=',1)[1].splitlines()[0]);(OUT/'duplicates.json').write_text(json.dumps(result,indent=2)+'\n')
 elif action=='broker-failure':
  assert not (OUT/'broker-failure.json').exists(),'Broker failure acceptance already exists; inspect before repeating.'
  setup=browser('broker-setup');sid=setup['job_id']
  code='SID='+str(sid)+'\n'+'''import json
from unittest.mock import patch
from kombu import Connection
from cpjudge.models import ImportJob
from cpjudge.conversion import queue_conversion
from cpjudge.tasks import convert_upload
j=ImportJob.objects.select_related('owner').get(pk=SID);assert j.status=='uploaded'
original=convert_upload.apply_async
with Connection('redis://127.0.0.1:1/1',connect_timeout=1,transport_options={'socket_connect_timeout':1,'socket_timeout':1,'retry_on_timeout':False}) as unavailable:
 def refused(*args,**kwargs):
  kwargs.update(connection=unavailable,retry=False)
  return original(*args,**kwargs)
 with patch.object(convert_upload,'apply_async',side_effect=refused):queue_conversion(j.owner,j.pk)
j.refresh_from_db();assert j.status=='failed' and j.attempt==1
assert 'queue is unavailable' in j.error and '127.0.0.1' not in j.error
print('Real Kombu broker connection refusal persisted a safe failed attempt after commit.')
'''
  driver.shell('real-broker-connection-refusal',code)
  result=browser('broker-retry');assert result['terminal_status']=='succeeded' and result['attempt']==2
  (OUT/'broker-failure.json').write_text(json.dumps({'status':'PASS','job_id':sid,'actual_Kombu_connection_refused':True,'safe_failed_attempt':1,'browser_retry_succeeded_attempt':2,'project_Redis_not_stopped_or_reconfigured':True},indent=2)+'\n')
 elif action=='interruption':
  assert not (OUT/'interruption.json').exists(),'Interruption acceptance already exists; inspect it before repeating.'
  # The held global lock gives a deterministic window after the actual task claim.
  # No converter exists yet, so killing only Celery cannot orphan a child process.
  driver.docker('hold-task-owned-conversion-lock','exec','-d',SITE,'python','-c',
   "import fcntl,os,time;from pathlib import Path;p=Path('/app/private-cpj-imports/.conversion.lock');f=p.open('a');fcntl.flock(f,fcntl.LOCK_EX);r=Path('/tmp/c07-lock-holder.pid');r.write_text(str(os.getpid()));r.chmod(0o600);time.sleep(60)")
  driver.docker('wait-task-owned-lock-ready','exec',SITE,'python','-c',"import time;from pathlib import Path\nfor _ in range(50):\n if Path('/tmp/c07-lock-holder.pid').exists():break\n time.sleep(.1)\nelse:raise RuntimeError('Conversion lock holder did not become ready')")
  try:
   result=browser('queue-only');sid=result['job_id']
   code='SID='+str(sid)+'\n'+'''import os,signal,time,json
from pathlib import Path
from cpjudge.models import ImportJob
for _ in range(20):
 j=ImportJob.objects.get(pk=SID)
 if j.status=='running':break
 if j.status=='failed':raise AssertionError('Task already failed before interruption')
 time.sleep(.1)
assert j.status=='running'
pids=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:args=(p/'cmdline').read_bytes().split(bytes([0]))
 except OSError:continue
 if b'--hostname=b02@site' in args and b'worker' in args:pids.append(int(p.name))
assert len(pids)==1
os.kill(pids[0],signal.SIGKILL)
print('Actual running Celery conversion task interrupted; native judge untouched.')
'''
   driver.shell('interrupt-only-celery-running-task',code)
  finally:
   driver.docker('release-task-owned-conversion-lock','exec',SITE,'python','-c',"import os,signal;from pathlib import Path;p=Path('/tmp/c07-lock-holder.pid');pid=int(p.read_text());os.kill(pid,signal.SIGTERM);p.unlink()")
  code='SID='+str(sid)+'\n'+'''import datetime,json
from django.utils import timezone
from cpjudge.models import ImportJob
from cpjudge.conversion import reconcile_imports
j=ImportJob.objects.get(pk=SID);assert j.status=='running'
# Accelerate the lease clock on this task-owned fixture; do not alter results.
ImportJob.objects.filter(pk=SID,status='running').update(started_at=timezone.now()-datetime.timedelta(seconds=181))
assert reconcile_imports(job_id=SID)==1
j.refresh_from_db();assert j.status=='failed' and 'interrupted' in j.error
print('Actual interrupted attempt reconciled to safe failed state.')
'''
  driver.shell('reconcile-real-interrupted-task',code)
  driver.docker('restart-only-missing-celery','exec',SITE,'python','/tmp/b02_process.py','start')
  result=browser('retry');assert result['terminal_status']=='succeeded' and result['attempt']>=2
  (OUT/'interruption.json').write_text(json.dumps({'status':'PASS','job_id':sid,'actual_running_celery_interrupted':True,'accelerated_fixture_lease_for_reconciliation':True,'browser_retry_terminal_status':'succeeded','attempt':result['attempt'],'judge_process_untouched':True},indent=2)+'\n')
 else:raise SystemExit('Unknown C07 validation action')
