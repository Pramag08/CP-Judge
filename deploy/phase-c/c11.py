"""C11 operator checks. Secret-bearing subprocess output stays in ignored build/."""
import gzip,hashlib,json,os,sys,time,grp,shlex
from pathlib import Path
if grp.getgrnam('docker').gr_gid not in [os.getgid(),*os.getgroups()]:
 os.execvp('sg',['sg','docker','-c',shlex.join([sys.executable,'-B',str(Path(__file__).resolve()),*sys.argv[1:]])])
import c05 as d
ROOT=d.ROOT;HERE=d.HERE;SITE=d.SITE;WORKER='cpjudge-b03-worker'
sys.path.insert(0,str(ROOT))
WORK=ROOT/'build/phase-c-c11-1';OUT=ROOT/'reports/phase-c-c11-1'
WORK.mkdir(mode=0o700,parents=True,exist_ok=True);WORK.chmod(0o700);OUT.mkdir(parents=True,exist_ok=True)
d.WORK=WORK;d.OUT=OUT
IMAGE='sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8'

def inspect(name):return json.loads(d.docker('inspect-'+name,'inspect',name))[0]
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
def snapshot():
 assert not (WORK/'before.json').exists(),'Do not overwrite snapshot'
 d.shell('snapshot-idle-existing-data',"""import json
from pathlib import Path
from django.apps import apps
from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
p=Path('/tmp/c11-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('Private all-model baseline saved; no active judging.')
""")
 d.docker('save-private-baseline','cp',SITE+':/tmp/c11-before.json',str(WORK/'before.json'));(WORK/'before.json').chmod(0o600)
 objs={n:inspect(n) for n in (SITE,WORKER,'cpjudge-b01-db','cpjudge-b01-redis')}
 assert objs[WORKER]['Image']==IMAGE
 p=WORK/'containers-before.json';p.write_text(json.dumps(objs));p.chmod(0o600)
 from tools.site_problem import file_manifest
 protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'build/b03-worker-1/private/worker.json',ROOT/'build/b03-worker-1/private/config.yml',ROOT/'build/b05-problem-1/private/registry.json']}
 protected['worker_files']=file_manifest(ROOT/'build/b03-worker-1/problems')
 p=WORK/'files-before.json';p.write_text(json.dumps(protected));p.chmod(0o600)
 raw=d.docker('private-db-backup','exec','cpjudge-b01-db','sh','-c','exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
 p=WORK/'database.sql.gz'
 with p.open('xb') as f:os.chmod(p,0o600);f.write(gzip.compress(raw))
 assert gzip.decompress(p.read_bytes())==raw and b'-- Dump completed on' in raw
 for rel in ('judge/bridge/judge_handler.py','judge/bridge/judge_list.py','templates/submission/status-testcases.html'):
  target=WORK/'originals'/rel;target.parent.mkdir(parents=True,exist_ok=True)
  d.docker('snapshot-source-'+Path(rel).name,'cp',SITE+':/app/'+rel,str(target))
 save('backup.json',{'readable_private_backup':True,'restore_tested':False,'worker_image':IMAGE,'idle_before_changes':True})


BRIDGE_STOP = """import os,signal,time
from pathlib import Path
found=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:args=(p/'cmdline').read_bytes().split(b'\\0')
 except OSError:continue
 if args[1:3]==[b'manage.py',b'runbridged']:
  found.append(int(p.name));os.kill(int(p.name),signal.SIGTERM)
assert len(found)==1
for _ in range(100):
 if all(not Path('/proc',str(pid),'cmdline').exists() or not Path('/proc',str(pid),'cmdline').read_bytes() for pid in found):break
 time.sleep(.1)
else:raise RuntimeError('Bridge did not stop')
"""
HTTP_STOP = BRIDGE_STOP.split('assert len(found)==1')[0].replace("b'runbridged'", "b'runserver'")+"assert len(found)==1"

if __name__=='__main__':
 action=sys.argv[1]
 if action=='backup':snapshot()
 elif action=='stage':
  assert (WORK/'before.json').exists()
  for name in ('readiness_wire.py','bridge_readiness.py','c11_tests.py'):
   d.docker('stage-'+name,'cp',str(HERE/'cpjudge'/name),SITE+':/app/cpjudge/'+name)
  for name,target in (('c11_worker.py','/tmp/c11_worker.py'),('cpjudge/readiness_wire.py','/tmp/readiness_wire.py')):
   d.docker('stage-worker-'+Path(name).name,'exec','-i',WORKER,'/env/bin/python3','-c',
       "import os,sys;from pathlib import Path;p=Path(sys.argv[1]);p.write_bytes(sys.stdin.buffer.read());p.chmod(0o600)",target,data=(HERE/name).read_bytes())
  d.docker('stage-worker-verifier-tests','cp',str(HERE/'c11_worker.py'),SITE+':/app/cpjudge/c11_worker.py')
  d.docker('stage-overlay-for-isolated-tests','cp',str(HERE/'c11_overlay.py'),SITE+':/tmp/c11_overlay.py')
  d.docker('apply-overlay-for-isolated-tests','exec',SITE,'python','/tmp/c11_overlay.py')
  raw=d.docker('worker-runtime-inventory','exec',WORKER,'/bin/bash','-c','. ~judge/.profile; export HOME=/tmp; exec /env/bin/python3 -B /tmp/c11_worker.py --inventory')
  inventory=json.loads(raw.decode().split('C11_INVENTORY=',1)[1].splitlines()[0])
  registry=json.loads((ROOT/'build/b05-problem-1/private/registry.json').read_text())
  manifest=registry['manifest'];assert manifest['native_code']=='pv000000000000000001'
  enrollment={'schema':1,'worker_name':'cpjudge-local-worker','inventory':inventory,
              'legacy':{manifest['native_code']:{**registry,'checker':'CPP23'}}}
  path=WORK/'enrollment.json'
  if path.exists():assert json.loads(path.read_text())==enrollment,'Runtime enrollment changed; explicit review required'
  else:path.write_text(json.dumps(enrollment));path.chmod(0o600)
  d.docker('stage-private-enrollment','cp','-a',str(path),SITE+':/app/cpj-readiness.json')
  d.docker('verify-private-enrollment-owner','exec',SITE,'python','-c',"import os;from pathlib import Path;p=Path('/app/cpj-readiness.json');assert p.stat().st_uid==os.getuid() and p.stat().st_mode & 0o777==0o600;assert p.read_bytes()")
  save('runtime.json',{'worker_image':IMAGE,'source_pin':inventory['source_pin'],
       'executors':list(inventory['runtime']),'config_and_command_hashes_pinned':True})
 elif action=='tests':
  d.docker('stage-current-c11-tests','cp',str(HERE/'cpjudge/c11_tests.py'),SITE+':/app/cpjudge/c11_tests.py')
  d.docker('focused-native-c11-tests','exec','--user','1000:1000',SITE,'python','manage.py','test',
   'cpjudge.c11_tests','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='activate':
  assert (WORK/'before.json').exists() and (WORK/'enrollment.json').exists()
  d.shell('guard-idle-code-reload',"from judge.models import Submission\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nprint('No active submissions.')")
  os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
  d.run('stop-native-worker-idle',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'stop'])
  d.docker('stop-only-idle-bridge','exec','-i',SITE,'python','-c',BRIDGE_STOP)
  d.docker('stage-native-overlay','cp',str(HERE/'c11_overlay.py'),SITE+':/tmp/c11_overlay.py')
  d.docker('install-native-overlay','exec',SITE,'python','/tmp/c11_overlay.py')
  d.docker('start-native-bridge','exec','-d',SITE,'sh','-c','exec python manage.py runbridged >> /tmp/b02-bridge.log 2>&1')
  time.sleep(2)
  (WORK/'enabled').write_text('C11 private authenticated exact-version readiness enabled.\n')
  d.run('start-native-worker-and-private-verifier',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'start'])
  # Template change requires only the native local HTTP process reload.
  d.docker('stop-only-http','exec',SITE,'python','-c',HTTP_STOP)
  d.docker('start-only-http','exec','-d',SITE,'sh','-c','exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/c11-http.log 2>&1')
 elif action=='diagnose':
  raw=d.shell('current-c11-state',"from judge.models import Submission\nimport json\ns=Submission.objects.get(pk=16)\nprint('C11_CURRENT='+json.dumps({'status':s.status,'result':s.result,'cases':s.test_cases.count()}))")
  print(raw.decode().split('C11_CURRENT=',1)[1].splitlines()[0])
  d.docker('private-bridge-diagnostic','exec',SITE,'cat','/tmp/b02-bridge.log')
  d.docker('private-worker-diagnostic','exec',WORKER,'cat','/tmp/c11-readiness.log')
 elif action=='refresh-verifier':
  d.run('stop-only-private-verifier',['python3','-B',str(ROOT/'deploy/site-local/worker_readiness.py'),'stop'])
  for name in ('c11_tests.py',):
   d.docker('stage-'+name,'cp',str(HERE/'cpjudge'/name),SITE+':/app/cpjudge/'+name)
  d.docker('stage-worker-verifier-regression','cp',str(HERE/'c11_worker.py'),SITE+':/app/cpjudge/c11_worker.py')
  d.run('start-only-corrected-private-verifier',['python3','-B',str(ROOT/'deploy/site-local/worker_readiness.py'),'start'])
 elif action=='preserve':
  from c11_preserve import run
  run()
 elif action=='finish':
  from c11_live import finish
  finish()
 elif action=='final-checks':
  names=['readiness_wire.py','bridge_readiness.py','c11_tests.py']
  expected={name:hashlib.sha256((HERE/'cpjudge'/name).read_bytes()).hexdigest() for name in names}
  code="from pathlib import Path\nimport hashlib,json\nnames="+repr(names)+"\nprint('C11_HASHES='+json.dumps({n:hashlib.sha256((Path('/app/cpjudge')/n).read_bytes()).hexdigest() for n in names}))"
  raw=d.docker('verify-deployed-site-source','exec',SITE,'python','-c',code)
  actual=json.loads(raw.decode().split('C11_HASHES=',1)[1].splitlines()[0]);assert actual==expected
  raw=d.docker('verify-deployed-worker-source','exec',WORKER,'/env/bin/python3','-c',"from pathlib import Path;import hashlib,json;print(json.dumps({n:hashlib.sha256((Path('/tmp')/n).read_bytes()).hexdigest() for n in ('c11_worker.py','readiness_wire.py')}))")
  actual_worker=json.loads(raw)
  assert actual_worker['c11_worker.py']==hashlib.sha256((HERE/'c11_worker.py').read_bytes()).hexdigest()
  assert actual_worker['readiness_wire.py']==expected['readiness_wire.py']
  testlog=sorted(WORK.glob('*focused-native-c11-tests.log'))[-1].read_text()
  assert 'Ran 27 tests' in testlog and '\nOK\n' in testlog and 'skipped=' not in testlog
  d.run('git-diff-whitespace',['git','diff','--check'])
  save('checks.json',{'status':'PASS','focused_tests':27,'skips':0,'site_pin':'604d60cfd764bc708b04ffd75b715a5398b91f8b',
       'worker_pin':'1245dc4158dbb9e906c4c103e1ea939e012ee79b','worker_image':IMAGE,
       'deployed_site_source_sha256':expected,'deployed_worker_source_sha256':actual_worker,
       'real_submissions':1,'submission_id':16,'actual_cases':103,'final_code_loaded_after_idle_reload':True,
       'no_C12_C13_work':True,'backup_restore':'NOT TESTED','inflight_crash_recovery':'NOT TESTED'})
 elif action=='profile-diagnose':
  raw=d.shell('native-profile-pointer-diagnostic',"""import json
from pathlib import Path
from judge.models import Submission,ContestParticipation
b=json.loads(Path('/tmp/c11-before.json').read_text());s=Submission.objects.get(pk=16);p=s.user
old=next(r for r in b['judge.profile'] if r['id']==p.pk)
print('C11_PROFILE='+json.dumps({'profile_id':p.pk,'current':p.current_contest_id,'before':old['current_contest_id'],
 'submission_contest':s.contest_object_id,'old_participation_count':len(b['judge.contestparticipation']),
 'current_participation_count':ContestParticipation.objects.count()}))
""")
  print(raw.decode().split('C11_PROFILE=',1)[1].splitlines()[0])
 elif action=='deep-diagnose':
  from c11_diagnose import run
  run()
 elif action=='live':
  from c11_live import run
  run()
 else:raise SystemExit('Unknown C11 action')
