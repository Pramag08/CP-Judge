"""Private C07 backup/migration and HTTP/Celery-only activation."""
import gzip,json,os,sys,time
from pathlib import Path
import c05 as d
ROOT=d.ROOT;HERE=d.HERE;WORK=ROOT/'build/phase-c-c07-1';OUT=ROOT/'reports/phase-c-c07-1'
WORK.mkdir(parents=True,exist_ok=True,mode=0o700);WORK.chmod(0o700);OUT.mkdir(parents=True,exist_ok=True)
d.WORK=WORK;d.OUT=OUT
if sys.argv[1]=='backup-migrate':
 assert not (WORK/'migration-receipt.json').exists(),'Inspect receipt; do not repeat migration'
 raw=d.docker('private-pre-migration-backup','exec','cpjudge-b01-db','sh','-c','exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
 path=WORK/(d.STAMP+'-database.sql.gz')
 with path.open('xb') as f:os.chmod(path,0o600);f.write(gzip.compress(raw))
 assert gzip.decompress(path.read_bytes())==raw and b'-- Dump completed on' in raw
 d.shell('pre-migration-private-snapshot',"""import json
from pathlib import Path
from django.apps import apps
from judge.models import Submission
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
p=Path('/tmp/c07-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('Private live-data snapshot captured.')
""")
 d.docker('stage-c07-app','cp',str(HERE/'cpjudge')+'/.',d.SITE+':/app/cpjudge')
 d.docker('generate-c07-migration','exec','--user','1000:1000',d.SITE,'python','manage.py','makemigrations','cpjudge','--noinput')
 d.docker('retain-c07-migration','cp',d.SITE+':/app/cpjudge/migrations/.',str(HERE/'cpjudge/migrations'))
 d.docker('apply-real-migration','exec',d.SITE,'python','manage.py','migrate','--noinput')
 (WORK/'migration-receipt.json').write_text(json.dumps({'backup':str(path.relative_to(ROOT)),'gzip_full_readback':True,'restore_tested':False,'migrations_applied':True}));(WORK/'migration-receipt.json').chmod(0o600)
 (OUT/'migration.json').write_text((WORK/'migration-receipt.json').read_text()+'\n')
elif sys.argv[1]=='finish-migrate':
 path=max(WORK.glob('*-database.sql.gz'));raw=gzip.decompress(path.read_bytes());assert b'-- Dump completed on' in raw
 d.docker('generate-c07-migration','exec','--user','1000:1000',d.SITE,'python','manage.py','makemigrations','cpjudge','--noinput')
 d.docker('retain-c07-migration','cp',d.SITE+':/app/cpjudge/migrations/.',str(HERE/'cpjudge/migrations'))
 d.docker('apply-real-migration','exec',d.SITE,'python','manage.py','migrate','--noinput')
 (WORK/'migration-receipt.json').write_text(json.dumps({'backup':str(path.relative_to(ROOT)),'gzip_full_readback':True,'restore_tested':False,'migrations_applied':True}));(WORK/'migration-receipt.json').chmod(0o600)
 (OUT/'migration.json').write_text((WORK/'migration-receipt.json').read_text()+'\n')
elif sys.argv[1]=='activate':
 assert (WORK/'migration-receipt.json').exists()
 d.docker('stage-current-app','cp',str(HERE/'cpjudge')+'/.',d.SITE+':/app/cpjudge')
 d.docker('stage-current-policy','cp',str(HERE/'native_settings.py'),d.SITE+':/app/dmoj/cpj_native_settings.py')
 d.docker('retain-celery-lifecycle-config','cp',str(ROOT/'deploy/site-local/b02_process.py'),d.SITE+':/tmp/b02_process.py')
 d.docker('restart-only-http-and-celery','exec','-i',d.SITE,'python',data=b'''import os,signal,time,subprocess
from pathlib import Path
celery=[];http=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:a=(p/'cmdline').read_bytes().split(bytes([0]))
 except OSError:continue
 if a[1:3]==[b'manage.py',b'runserver']:http.append(int(p.name))
 if b'--hostname=b02@site' in a and b'worker' in a:celery.append(int(p.name))
assert len(http)==len(celery)==1
for pid in http+celery:os.kill(pid,signal.SIGTERM)
for _ in range(100):
 if all(not Path('/proc/'+str(pid)).exists() or Path('/proc/'+str(pid)+'/stat').read_text().split()[2]=='Z' for pid in http+celery):break
 time.sleep(.1)
else:raise RuntimeError('Affected process did not stop')
for name,args in [('http',['python','manage.py','runserver','0.0.0.0:8000','--noreload']),('celery',['celery','-A','dmoj_celery','worker','--pool=solo','--concurrency=1','--prefetch-multiplier=1','-Q','celery,cpj_import','--loglevel=INFO','--hostname=b02@site'])]:
 fd=os.open('/tmp/c07-'+name+'.log',os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o600)
 subprocess.Popen(args,cwd='/app',stdout=fd,stderr=fd,start_new_session=True);os.close(fd)
print('Only HTTP/Celery reloaded; bridge and judge processes retained.')
''')
elif sys.argv[1]=='preserve':
 raw=d.shell('preexisting-live-rows-preserved',"""import json
from pathlib import Path
from django.apps import apps
before=json.loads(Path('/tmp/c07-before.json').read_text())
allowed={'auth.user':{'last_login'},'judge.profile':{'last_access','ip'},'judge.judge':{'ping','load','last_ip'},'cpjudge.identity':{'generation'}}
checked=0
for label,oldrows in before.items():
 if label=='sessions.session':continue
 model=apps.get_model(label);pk=model._meta.pk.attname
 rows={r[pk]:r for r in json.loads(json.dumps(list(model.objects.all().values()),default=str))}
 for old in oldrows:
  assert old[pk] in rows, 'Existing row removed: '+label
  delta={k for k in old if old[k]!=rows[old[pk]][k]}
  assert delta<=allowed.get(label,set()),'Unexpected existing-row changes: '+label+':'+','.join(sorted(delta))
  checked+=1
print('C07_PRESERVATION='+json.dumps({'status':'PASS','models_checked':len(before),'existing_rows_checked':checked,'account_passwords_college_ids_submissions_results_keys_preserved':True,'allowed_changes':'native login/access/session generation and judge liveness only'}))
""")
 result=json.loads(raw.decode().split('C07_PRESERVATION=',1)[1].splitlines()[0])
 (OUT/'preservation.json').write_text(json.dumps(result,indent=2)+'\n')
 d.docker('real-migration-consistency','exec',d.SITE,'python','manage.py','makemigrations','--check','--dry-run')
else:raise SystemExit('Unknown action')
