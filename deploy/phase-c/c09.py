"""C09 focused validation/activation; all subprocess output stays private."""
import hashlib,json,os,sys
from pathlib import Path
import c05 as d
ROOT=d.ROOT;HERE=d.HERE;SITE=d.SITE
WORK=ROOT/'build/phase-c-c09-1';OUT=ROOT/'reports/phase-c-c09-1'
WORK.mkdir(mode=0o700,parents=True,exist_ok=True);WORK.chmod(0o700);OUT.mkdir(parents=True,exist_ok=True)
d.WORK=WORK;d.OUT=OUT

def snapshot():
 assert not (OUT/'containers-before.json').exists(), 'Snapshot exists; inspect rather than replace the baseline'
 d.shell('snapshot-existing-rows', '''import json
from pathlib import Path
from django.apps import apps
from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
p=Path('/tmp/c09-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('C09 private snapshot retained.')
''')
 data={}
 for name in (SITE,'cpjudge-b03-worker','cpjudge-b01-db','cpjudge-b01-redis'):
  obj=json.loads(d.docker('snapshot-container-'+name,'inspect',name))[0]
  data[name]={'id':obj['Id'],'image':obj['Image'],'started':obj['State']['StartedAt'],'config_hash':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()}
 (OUT/'containers-before.json').write_text(json.dumps(data,indent=2)+'\n')

def stage():
 for name in ('presentation.py','statement.py','native.py','urls.py','c09_tests.py'):
  d.docker('stage-'+name,'cp',str(HERE/'cpjudge'/name),SITE+':/app/cpjudge/'+name)
 for name in ('import_confirm.html','statement.html'):
  d.docker('stage-'+name,'cp',str(HERE/'cpjudge/templates/cpjudge'/name),SITE+':/app/cpjudge/templates/cpjudge/'+name)

if __name__=='__main__':
 action=sys.argv[1]
 if action=='snapshot':snapshot()
 elif action=='stage':stage()
 elif action=='tests':
  d.docker('focused-c09-and-regressions','exec','--user','1000:1000',SITE,'python','manage.py','test','cpjudge.c09_tests.StatementTests','cpjudge.tests.PresentationTests','cpjudge.c07_tests.ConversionTests','cpjudge.integration_tests.NativeUploadHTTPTests','--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='activate':
  source=(HERE/'c05.py').read_text();body=source.split("elif action=='restart-web':",1)[1].split("elif action=='browser':",1)[0]
  exec('if True:'+body,d.__dict__)
 elif action=='browser':
  import struct,zlib
  folder=WORK/'browser'/d.STAMP;folder.mkdir(mode=0o700,parents=True)
  def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
  image=folder/'image.png';image.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,2,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\xff\x00\x00\xff\x00\x00'*2))+chunk(b'IEND',b''))
  d.docker('actual-c09-chromium','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={ROOT/"build/phase-c-checkpoint1-1/accounts.json"},dst=/run/accounts.json,readonly',
   '--mount',f'type=bind,src={ROOT/"build/phase-c-c07-1/package.zip"},dst=/run/package.zip,readonly',
   '--mount',f'type=bind,src={ROOT/"local-packages/gaming-grid.zip"},dst=/run/real.zip,readonly',
   '--mount',f'type=bind,src={image},dst=/run/image.png,readonly',
   '--mount',f'type=bind,src={HERE/"c09_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
  (OUT/'browser.json').write_text((folder/'browser.json').read_text())
 elif action=='state-checks':
  data=json.loads((OUT/'browser.json').read_text());job=data['jobs']['malicious']
  folder=WORK/'states'/d.STAMP;folder.mkdir(mode=0o700,parents=True)
  raw=d.shell('construct-c09-stale-states-and-retry-fixture','JOB='+str(job)+'\n'+"""import json,secrets
from cpjudge.models import ImportJob
from django.utils import timezone
source=ImportJob.objects.get(pk=JOB);assert source.status=='succeeded' and source.attempt==1
assert not ImportJob.objects.filter(archive_key__startswith='c09-state-').exists(),'Inspect existing state fixtures before repeating'
receipt={}
for state in ('queued','running','failed'):
 j=ImportJob.objects.create(owner=source.owner,contest=source.contest,package_sha256=secrets.token_hex(32),archive_key='c09-state-'+state,status=state,attempt=source.attempt,token=source.token,findings=source.findings,queued_at=timezone.now(),started_at=timezone.now())
 receipt[state]=j.pk
ImportJob.objects.filter(pk=source.pk).update(status='failed',error='Conversion service busy. Please retry.')
print('C09_STATES='+json.dumps(receipt))
""")
  fixture={'retry_job':job,'old_asset':data['asset_path'],'states':json.loads(raw.decode().split('C09_STATES=',1)[1].splitlines()[0])}
  (folder/'fixtures.json').write_text(json.dumps(fixture));(folder/'fixtures.json').chmod(0o600)
  d.docker('actual-c09-state-refresh-retry','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={ROOT/"build/phase-c-checkpoint1-1/accounts.json"},dst=/run/accounts.json,readonly',
   '--mount',f'type=bind,src={HERE/"c09_states_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
  (OUT/'states.json').write_text((folder/'states.json').read_text())
 elif action=='preserve':
  source=(HERE/'c07_activate.py').read_text();body=source.split('raw=d.shell(\'preexisting-live-rows-preserved\',"""',1)[1].split('""")',1)[0].replace('/tmp/c07-before.json','/tmp/c09-before.json').replace('C07_PRESERVATION','C09_PRESERVATION')
  raw=d.shell('preserve-existing-rows',body)
  result=json.loads(raw.decode().split('C09_PRESERVATION=',1)[1].splitlines()[0]);(OUT/'preservation.json').write_text(json.dumps(result,indent=2)+'\n')
  before=json.loads((OUT/'containers-before.json').read_text())
  for name,baseline in before.items():
   obj=json.loads(d.docker('verify-container-'+name,'inspect',name))[0]
   current={'id':obj['Id'],'image':obj['Image'],'started':obj['State']['StartedAt'],'config_hash':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()}
   assert current==baseline
  (OUT/'containers-preserved.json').write_text(json.dumps({'status':'PASS','container_ids_images_configuration_start_times_unchanged':True},indent=2)+'\n')
 else:raise SystemExit('Unknown C09 action')
