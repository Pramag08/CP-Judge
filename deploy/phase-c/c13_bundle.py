"""Sequential C13/C18/C19 operator driver. Private command output only."""
import gzip,json,os,sys,time
from pathlib import Path
import c05 as d
ROOT,HERE,SITE=d.ROOT,d.HERE,d.SITE
WORK=ROOT/'build/phase-c-c13-identity-1';OUT=ROOT/'reports/phase-c-c13-identity-1'
WORK.mkdir(parents=True,exist_ok=True,mode=0o700);WORK.chmod(0o700);OUT.mkdir(parents=True,exist_ok=True)
d.WORK,d.OUT=WORK,OUT

def save(name,data): (OUT/name).write_text(json.dumps(data,indent=2)+'\n')
def stage():
 d.docker('stage-current-app','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
def reload():
 code=(HERE/'c07_activate.py').read_text().split("data=b'''",1)[1].split("''')",1)[0]
 d.docker('reload-http-celery-idle','exec','-i',SITE,'python',data=code.encode())
 import urllib.request
 for _ in range(60):
  try:
   with urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/',timeout=2) as response:
    if response.status==200:break
  except Exception:time.sleep(.5)
 else:raise RuntimeError('HTTP restart failed')
def shell_file(name): return d.shell(name,(HERE/(name+'.py')).read_text())

if __name__=='__main__':
 action=sys.argv[1]
 if action=='backup':
  assert not (WORK/'before.json').exists()
  raw=d.docker('fresh-private-full-backup','exec','cpjudge-b01-db','sh','-c','exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
  p=WORK/'database.sql.gz'
  with p.open('xb') as f:os.chmod(p,0o600);f.write(gzip.compress(raw))
  assert gzip.decompress(p.read_bytes())==raw and b'-- Dump completed on' in raw
  d.shell('private-baseline-and-c11-live-verification','''import json,hashlib
from pathlib import Path
from django.apps import apps
from judge.models import Submission,Judge
from cpjudge.bridge_readiness import CONFIG,requirements
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
assert Judge.objects.get(name='cpjudge-local-worker').online
requirements('pv000000000000000001','CPP23')
p=Path('/tmp/c13-identity-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('Existing C11 gate/configuration and online worker confirmed; private baseline saved.')
''')
  d.docker('retain-private-baseline','cp',SITE+':/tmp/c13-identity-before.json',str(WORK/'before.json'));(WORK/'before.json').chmod(0o600)
  save('backup.json',{'full_private_gzip_readback':True,'c11_historical_acceptance_inspected':True,'c11_current_configuration_online_worker':True,'restore_tested':False})
 elif action=='backup-next':
  label=sys.argv[2];assert label in ('c18','c19')
  raw=d.docker('fresh-private-'+label+'-backup','exec','cpjudge-b01-db','sh','-c','exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
  p=WORK/(label+'-database.sql.gz')
  with p.open('xb') as f:os.chmod(p,0o600);f.write(gzip.compress(raw))
  assert gzip.decompress(p.read_bytes())==raw and b'-- Dump completed on' in raw
 elif action=='stage':stage()
 elif action=='migration':
  assert (WORK/'before.json').exists()
  d.docker('generate-task-migration','exec','--user','1000:1000',SITE,'python','manage.py','makemigrations','cpjudge','--noinput')
  d.docker('retain-task-migration','cp',SITE+':/app/cpjudge/migrations/.',str(HERE/'cpjudge/migrations'))
  d.docker('apply-task-migration','exec',SITE,'python','manage.py','migrate','--noinput')
 elif action=='reload':reload()
 elif action=='bridge-reload':
  d.shell('idle-guard-before-bridge-reload',"from judge.models import Submission\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()")
  d.run('stop-idle-native-worker',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'stop'])
  import c11
  d.WORK,d.OUT=WORK,OUT
  d.docker('stop-idle-bridge','exec','-i',SITE,'python','-c',c11.BRIDGE_STOP)
  d.docker('start-readiness-bridge','exec','-d',SITE,'sh','-c','exec python manage.py runbridged >> /tmp/b02-bridge.log 2>&1')
  time.sleep(2)
  d.run('start-native-worker-verifier',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'start'])
 elif action=='install-probe-version':
  raw=d.shell('verify-c10-version-for-private-worker-install', '''import json
from cpjudge.models import ProblemVersion
from cpjudge.publication import verify_native,destination
v=ProblemVersion.objects.get(pk=2);assert verify_native(v)
assert not v.problem.is_public and not v.problem.allowed_languages.exists() and not v.problem.contests.exists()
print('INSTALL='+json.dumps({'path':str(destination(v)),'code':v.code,'files':v.manifest['files']}))
''')
  data=json.loads(raw.decode().split('INSTALL=',1)[1].splitlines()[0]);stagepath=WORK/('private-install-'+d.STAMP)
  assert not stagepath.exists()
  raw=d.docker('copy-private-staged-version','exec',SITE,'tar','-cf','-','-C',data['path'],'.')
  import io,tarfile
  stagepath.mkdir(mode=0o700)
  with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
   for entry in archive:
    dest=stagepath/entry.name
    assert dest.resolve().is_relative_to(stagepath.resolve())
    if entry.isdir():dest.mkdir(parents=True,exist_ok=True)
    else:
     assert entry.isfile();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.extractfile(entry).read())
  sys.path.insert(0,str(ROOT))
  from tools.site_problem import install_directory
  install_directory(stagepath,ROOT/'build/b03-worker-1/problems',data['code'],data['files'],durable=True)
  d.docker('refresh-native-advertisement','kill','--signal','USR2','cpjudge-b03-worker')
  save('probe-install.json',{'version_id':2,'native_code':data['code'],'private_immutable_hash_verified':True,'participant_access_enabled':False})
 elif action=='tests':
  d.docker('focused-task-tests','exec','--user','1000:1000',SITE,'python','manage.py','test',*sys.argv[2:],'--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='browser':
  folder=WORK/('browser-'+sys.argv[2]);folder.mkdir(mode=0o700,exist_ok=True)
  d.docker('browser-'+sys.argv[2],'run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={ROOT/"build/phase-c-checkpoint1-1/accounts.json"},dst=/run/accounts.json,readonly',
   '--mount',f'type=bind,src={HERE/(sys.argv[2]+"_browser.py")},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
  save(sys.argv[2]+'-browser.json',json.loads((folder/'result.json').read_text()))
 elif action=='c19-live':
  import subprocess
  attempt=sys.argv[2] if len(sys.argv)>2 else ''
  assert attempt in ('','retry1')
  folder=WORK/('browser-c19'+attempt);folder.mkdir(mode=0o700,exist_ok=True)
  assert not (folder/'ready-reset').exists(),'Resume existing browser evidence; do not repeat reset.'
  d.docker('private-provisioned-credential-for-browser','cp',SITE+(':/tmp/c19-reset-account.json' if attempt else ':/tmp/c19-new-account.json'),str(folder/'new-account.json'))
  (folder/'new-account.json').chmod(0o600)
  args=['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={HERE/"c19_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py']
  logfile=WORK/(d.STAMP+'-browser-c19.log')
  with logfile.open('wb') as log:
   logfile.chmod(0o600);proc=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT)
   for _ in range(120):
    if (folder/'ready-reset').exists():break
    if proc.poll() is not None:raise RuntimeError('Browser ended before reset; inspect private log')
    time.sleep(.5)
   else:raise RuntimeError('No initial login receipt; do not reset')
   d.shell('c19-reset'+attempt,'C19_ATTEMPT='+repr(attempt)+'\n'+(HERE/'c19_reset.py').read_text())
   d.docker('private-reset-credential-for-browser','cp',SITE+':/tmp/c19-reset-account'+attempt+'.json',str(folder/'reset.json'))
   (folder/'reset.json').chmod(0o600)
   proc.wait(timeout=150)
  records=json.loads((OUT/'commands.json').read_text());records.append({'name':'actual-c19-browser','exit_status':proc.returncode,'private_log':str(logfile.relative_to(ROOT))});save('commands.json',records)
  assert proc.returncode==0,'Inspect private browser evidence; do not repeat reset'
  save('c19-browser.json',json.loads((folder/'result.json').read_text()))
 elif action=='participant-browser':
  folder=WORK/'participant-browser';folder.mkdir(mode=0o700,exist_ok=True)
  # Existing admission is resumed read-only, never resubmitted.
  accounts=json.loads((ROOT/'build/phase-c-checkpoint1-1/accounts.json').read_text())
  baseline=json.loads((WORK/'before.json').read_text());user=next(r for r in baseline['auth.user'] if r['username']==accounts['accounts']['p']['username'])
  private=json.loads((WORK/'c18-private-inventory.json').read_text());accounts['accounts']['p']['login']=private['mapping'][str(user['id'])]
  path=folder/'accounts.json';path.write_text(json.dumps(accounts));path.chmod(0o600)
  source=ROOT/'build/a03-judge-1/pipeline/problems/gaming-grid/solutions/reference.cpp';assert source.is_file()
  d.docker('normal-email-participant-native-submission','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={source},dst=/run/reference.cpp,readonly',
   '--mount',f'type=bind,src={HERE/"live_submission.py"},dst=/tests/native_submission.py,readonly',
   '--mount',f'type=bind,src={HERE/"c19_submission_browser.py"},dst=/tests/browser.py,readonly',
   *(['--mount',f'type=bind,src={folder/"submission-receipt.json"},dst=/run/receipt.json,readonly'] if (folder/'submission-receipt.json').exists() else []),
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
  save('participant-browser.json',json.loads((folder/'result.json').read_text()))
 elif action=='final-checks':
  import hashlib
  names=['identity.py','email_identity.py','views.py','models.py','sessions.py','native.py','probes.py','bridge_readiness.py','tasks.py','imports.py','admin.py','urls.py']
  expected={n:hashlib.sha256((HERE/'cpjudge'/n).read_bytes()).hexdigest() for n in names}
  raw=d.docker('deployed-final-source-identity','exec',SITE,'python','-c',"import hashlib,json;from pathlib import Path;print(json.dumps({n:hashlib.sha256((Path('/app/cpjudge')/n).read_bytes()).hexdigest() for n in "+repr(names)+"}))")
  assert json.loads(raw)==expected
  d.docker('migration-consistency-final','exec',SITE,'python','manage.py','makemigrations','--check','--dry-run')
  containers=json.loads((ROOT/'build/phase-c-c12-1/containers.json').read_text())
  for name,digest in containers.items():
   obj=json.loads(d.docker('container-preservation-'+name,'inspect',name))[0]
   actual=hashlib.sha256(json.dumps({k:obj[k] for k in ('Id','Image','Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()
   if digest!=actual:
    assert name=='cpjudge-b03-worker' and obj['HostConfig']['Dns']==[], 'Container configuration/sandbox changed'
    # Docker's container-network restart normalizes unset DNS null to [].
    obj['HostConfig']['Dns']=None
    actual=hashlib.sha256(json.dumps({k:obj[k] for k in ('Id','Image','Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()
    assert digest==actual,'Container configuration/sandbox changed'
  sys.path.insert(0,str(ROOT))
  from tools.site_problem import file_manifest
  registry=json.loads((ROOT/'build/b05-problem-1/private/registry.json').read_text())
  assert file_manifest(ROOT/'build/b03-worker-1/problems/pv000000000000000001')==registry['manifest']['files']
  logs=sorted(WORK.glob('*focused-task-tests.log'));final=logs[-1].read_text()
  assert 'Ran 16 tests' in final and '\nOK\n' in final and 'skipped=' not in final
  d.run('final-whitespace',['git','diff','--check'])
  save('final-checks.json',{'status':'PASS','final_focused_checks':16,'skips':0,'reused_c11_regressions_also_ran':27,
   'deployed_source_sha256':expected,'migration_consistency':True,'original_worker_problem_bytes_preserved':True,
   'container_ids_images_configuration_mounts_sandbox_match_c12_baseline':True,'worker_empty_dns_null_list_normalized_only':True,
   'site_pin':'604d60cfd764bc708b04ffd75b715a5398b91f8b','worker_pin':'1245dc4158dbb9e906c4c103e1ea939e012ee79b',
   'old_accounts_reset':False,'email_only_cutover':'BLOCKED','phase_c_complete':False})
 elif action=='shell':shell_file(sys.argv[2])
 else:raise SystemExit('Unknown action')
