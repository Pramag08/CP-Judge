"""C08 focused validation/activation; all subprocess output stays private."""
import hashlib,json,os,sys
from pathlib import Path
import c05 as d
ROOT=d.ROOT;HERE=d.HERE;SITE=d.SITE
WORK=ROOT/'build/phase-c-c08-1';OUT=ROOT/'reports/phase-c-c08-1'
WORK.mkdir(mode=0o700,parents=True,exist_ok=True);WORK.chmod(0o700);OUT.mkdir(parents=True,exist_ok=True)
d.WORK=WORK;d.OUT=OUT

def snapshot():
 assert not (OUT/'containers-before.json').exists(), 'Snapshot exists; inspect rather than replace the baseline'
 d.shell('snapshot-existing-rows', '''import json
from pathlib import Path
from django.apps import apps
from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
p=Path('/tmp/c08-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('C08 private snapshot retained.')
''')
 data={}
 for name in (SITE,'cpjudge-b03-worker','cpjudge-b01-db','cpjudge-b01-redis'):
  obj=json.loads(d.docker('snapshot-container-'+name,'inspect',name))[0]
  data[name]={'id':obj['Id'],'image':obj['Image'],'started':obj['State']['StartedAt'],'config_hash':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()}
 (OUT/'containers-before.json').write_text(json.dumps(data,indent=2)+'\n')

def stage():
 for name in ('compatibility.py','imports.py','conversion.py','convert_runner.py','views.py','c08_tests.py'):
  d.docker('stage-'+name,'cp',str(HERE/'cpjudge'/name),SITE+':/app/cpjudge/'+name)
 d.docker('stage-template','cp',str(HERE/'cpjudge/templates/cpjudge/import_confirm.html'),SITE+':/app/cpjudge/templates/cpjudge/import_confirm.html')

if __name__=='__main__':
 action=sys.argv[1]
 if action=='snapshot':snapshot()
 elif action=='stage':stage()
 elif action=='tests':
  d.docker('focused-native-c08-c07-tests','exec','--user','1000:1000',SITE,'python','manage.py','test','cpjudge.c08_tests','cpjudge.c07_tests.ConversionTests','cpjudge.integration_tests.NativeExtractionTests','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='activate':
  # Reuse C07's exact HTTP/Celery-only restart body; do not replay migration/staging.
  source=(HERE/'c07_activate.py').read_text();body=source.split("data=b'''",1)[1].split("''')",1)[0]
  d.docker('reload-only-http-celery','exec','-i',SITE,'python',data=body.encode())
 elif action=='fixtures':
  folder=WORK/'browser';folder.mkdir(mode=0o700,exist_ok=True)
  raw=d.shell('create-c08-owned-state-fixtures', """import json,secrets
from cpjudge.models import ImportJob
from django.utils import timezone
source=ImportJob.objects.get(pk=13)
assert source.status=='succeeded'
assert not ImportJob.objects.filter(archive_key__startswith='c08-state-').exists(), 'Inspect existing C08 fixtures instead of repeating'
receipt={}
for state in ('queued','running','failed'):
 j=ImportJob.objects.create(owner=source.owner,contest=source.contest,
  package_sha256=secrets.token_hex(32),archive_key='c08-state-'+state,
  status=state,attempt=2,token=secrets.token_hex(32),findings=source.findings,
  error='<script>window.c08Injected=1</script> /private/raw-log',
  queued_at=timezone.now(),started_at=timezone.now())
 receipt[state]=j.pk
print('C08_FIXTURES='+json.dumps(receipt))
""")
  result=json.loads(raw.decode().split('C08_FIXTURES=',1)[1].splitlines()[0]);(folder/'state-fixtures.json').write_text(json.dumps(result));(folder/'state-fixtures.json').chmod(0o600)
 elif action=='verify-output':
  data=json.loads((OUT/'browser.json').read_text())
  ids=[data['existing_success_job_id'],data['malicious-name_job_id'],data['groups_job_id']]
  raw=d.shell('verify-display-against-stored-output', 'IDS='+repr(ids)+'\n'+"""import json,math
from cpjudge.models import ImportJob
from cpjudge.compatibility import preview
from cpjudge.conversion import attempt_path
result=[]
for pk in IDS:
 j=ImportJob.objects.get(pk=pk);p=preview(j);assert p
 root=attempt_path(j.token)/'output';slug=j.findings['slug']
 r=json.loads((root/'conversion-report.json').read_text())
 import yaml
 c=yaml.safe_load((root/slug/'init.yml').read_text())
 assert p['test_count']==len(r['test_hashes'])
 assert p['sample_count']==len(r['samples'])
 assert p['seconds']==c['time_limit']==r['time_ms']/1000
 assert p['kib']==c['memory_limit']==math.ceil(r['memory_bytes']/1024)
 result.append({'job_id':pk,'tests':p['test_count'],'samples':p['sample_count'],
  'time':str(p['time_ms'])+' ms → '+str(p['seconds'])+' seconds',
  'memory':str(p['memory_bytes'])+' bytes → '+str(p['kib'])+' KiB (1 KiB = 1024 bytes; rounded up)',
  'standard':p['standard']+' ('+p['source_type']+')','sha256':j.package_sha256})
print('C08_OUTPUT='+json.dumps(result))
""")
  result=json.loads(raw.decode().split('C08_OUTPUT=',1)[1].splitlines()[0])
  displays=[data['existing_success_display'],data['malicious-name_success_display'],data['groups_success_display']]
  for actual,display in zip(result,displays):
   for field in ('tests','samples','time','memory','standard','sha256'):assert str(actual[field])==display[field], field
  (OUT/'output-agreement.json').write_text(json.dumps({'status':'PASS','actual_browser_equals_stored_conversion_report_and_init':True,'jobs':result},indent=2)+'\n')
 elif action=='browser':
  folder=WORK/'browser'/d.STAMP;folder.mkdir(mode=0o700,parents=True)
  fixture_path=WORK/'browser/state-fixtures.json'
  (folder/'state-fixtures.json').write_bytes(fixture_path.read_bytes());(folder/'state-fixtures.json').chmod(0o600)
  package=ROOT/'build/phase-c-c07-1/package.zip';assert package.exists()
  fixtures=json.loads((folder/'state-fixtures.json').read_text())
  d.shell('renew-only-c08-constructed-state-fixtures', 'IDS='+repr(fixtures)+'\n'+'''from cpjudge.models import ImportJob
from django.utils import timezone
for state,pk in IDS.items():
 j=ImportJob.objects.get(pk=pk);assert j.archive_key=='c08-state-'+state
 ImportJob.objects.filter(pk=pk).update(status=state,queued_at=timezone.now(),started_at=timezone.now())
print('Only C08 constructed state fixture leases renewed.')
''')
  d.docker('actual-c08-browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={ROOT/"build/phase-c-checkpoint1-1/accounts.json"},dst=/run/accounts.json,readonly',
   '--mount',f'type=bind,src={package},dst=/run/package.zip,readonly',
   '--mount',f'type=bind,src={ROOT/"build/phase-c-1/synthetic/groups.zip"},dst=/run/groups.zip,readonly',
   '--mount',f'type=bind,src={HERE/"c08_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
  (OUT/'browser.json').write_text((folder/'browser.json').read_text())
 elif action=='preserve':
  source=(HERE/'c07_activate.py').read_text();body=source.split('raw=d.shell(\'preexisting-live-rows-preserved\',"""',1)[1].split('""")',1)[0].replace('/tmp/c07-before.json','/tmp/c08-before.json').replace('C07_PRESERVATION','C08_PRESERVATION')
  raw=d.shell('preserve-existing-rows',body)
  result=json.loads(raw.decode().split('C08_PRESERVATION=',1)[1].splitlines()[0]);(OUT/'preservation.json').write_text(json.dumps(result,indent=2)+'\n')
  before=json.loads((OUT/'containers-before.json').read_text())
  for name,baseline in before.items():
   obj=json.loads(d.docker('verify-container-'+name,'inspect',name))[0]
   current={'id':obj['Id'],'image':obj['Image'],'started':obj['State']['StartedAt'],'config_hash':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()}
   assert current==baseline
  (OUT/'containers-preserved.json').write_text(json.dumps({'status':'PASS','container_ids_images_configuration_start_times_unchanged':True},indent=2)+'\n')
 else:raise SystemExit('Unknown C08 action')
