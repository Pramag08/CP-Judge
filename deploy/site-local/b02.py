"""Native B02 service lifecycle. Preserve existing B01 container/overlay/data."""
import argparse,datetime,grp,hashlib,json,os,shlex,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
WORK=ROOT/'build/b02-services-1';OUT=Path(os.environ.get('CPJ_SITE_REPORT_DIR', ROOT/'reports/b02-services-1'));SITE='cpjudge-b01-site';EVENT='cpjudge-b02-events'
def main():
 action=argparse.ArgumentParser();action.add_argument('action',choices=['setup','start','stop','status','verify','browser','resolve','restart','logs','audit','npm-audit','upgrade-event-deps']);args=action.parse_args()
 if grp.getgrnam('docker').gr_gid not in [os.getgid(),*os.getgroups()]:os.execvp('sg',['sg','docker','-c',shlex.join([sys.executable,'-B',str(Path(__file__).resolve()),args.action])])
 if (ROOT/'build/phase-c-checkpoint1-1/enabled').exists() and args.action in ('setup','upgrade-event-deps'):
  raise RuntimeError('Legacy event daemon is retired; checkpoint1 uses authenticated database polling.')
 OUT.mkdir(exist_ok=True,parents=True);WORK.mkdir(exist_ok=True,parents=True)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');logs=WORK/stamp;logs.mkdir()
 secrets=[]
 for p in (ROOT/'build/b01-site-1/private').glob('*.env'):secrets.extend(line.split('=',1)[1] for line in p.read_text().splitlines() if '=' in line)
 for row in json.loads((ROOT/'build/b01-site-1/private/accounts.json').read_text()).values():secrets.extend(row.values())
 def run(name,cmd,input=None,private=False):
  print(name+': running',flush=True);p=subprocess.run(cmd,input=input,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  raw=logs/(name+'.log');raw.write_text(p.stdout);raw.chmod(0o600)
  text=p.stdout
  for value in secrets:
   if len(value)>=6:text=text.replace(value,'[REDACTED]')
  target=OUT/'logs'/stamp/raw.name
  if not private:target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
  file=OUT/'commands.json';rows=json.loads(file.read_text()) if file.exists() else []
  rows.append({'action':args.action,'argv':cmd,'exit_status':p.returncode,'log':str((raw if private else target).relative_to(ROOT))});file.write_text(json.dumps(rows,indent=2)+'\n')
  print(name+': exit '+str(p.returncode),flush=True)
  if p.returncode and not (args.action=='npm-audit' and p.returncode==1):raise RuntimeError(name+' failed; see logs')
  return p.stdout
 def docker(name,*cmd,**kw):return run(name,['docker',*cmd],**kw)
 def shell(name,code):return docker(name,'exec','-i',SITE,'python','manage.py','shell',input=code)
 def exists():return subprocess.run(['docker','inspect',EVENT],capture_output=True).returncode==0
 def process(mode):return docker('native-processes-'+mode,'exec',SITE,'python','/tmp/b02_process.py',mode)
 if args.action=='upgrade-event-deps':
  work=WORK/'events';node=json.loads((ROOT/'reports/a09-site-1/base-pins.json').read_text())['node']
  shutil.copy2(HERE/'events/package-lock.json',WORK/'event-lock-before-security-fix.json')
  shutil.copy2(HERE/'events/package.json',work/'package.json')
  docker('event-stop-for-security-update','stop',EVENT)
  docker('fixed-event-lock-install','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--mount',f'type=bind,src={work},dst=/work','--workdir','/work','--env','npm_config_cache=/tmp/npm',node,'sh','-c','npm install --package-lock-only --ignore-scripts && npm ci --ignore-scripts')
  shutil.copy2(work/'package-lock.json',HERE/'events/package-lock.json')
  docker('fixed-event-restart','start',EVENT);time.sleep(2);return
 if args.action=='npm-audit':
  node=json.loads((ROOT/'reports/a09-site-1/base-pins.json').read_text())['node']
  print(docker('npm-security-audit','run','--rm','--mount',f'type=bind,src={WORK / "events"},dst=/work,readonly','--workdir','/work',node,'npm','audit','--json'));return
 if args.action=='audit':
  code="""import json,hashlib
from pathlib import Path
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.contrib.staticfiles import finders
loader=MigrationLoader(connection);loader.check_consistent_history(connection)
assert len(loader.applied_migrations)==202
rels=['templates/admin/base_site.html','templates/mathjax-load.html','templates/problem/raw.html','resources/martor-mathjax.js']
math={str(p.relative_to('/app/resources/vendor/mathjax-3.2.2')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/resources/vendor/mathjax-3.2.2').rglob('*') if p.is_file()}
print(json.dumps({'migrations':202,'overlay':{r:hashlib.sha256((Path('/app')/r).read_bytes()).hexdigest() for r in rels},'math':math,'migration_0153':hashlib.sha256(Path('/app/judge/migrations/0153_reconcile_model_metadata.py').read_bytes()).hexdigest()},indent=2))
"""
  text=shell('preserved-b01-runtime',code);data=json.loads(text[text.index('{'):])
  old=json.loads((ROOT/'reports/b01-followup-1/runtime-final.json').read_text())
  assert data['overlay']==old['runtime_overlay_sha256'] and data['math']==old['math_files_sha256'] and data['migration_0153']==old['migration_0153_sha256']
  docker('deployment-warnings','exec',SITE,'python','manage.py','check','--deploy','--database','default')
  (OUT/'runtime-preservation.json').write_text(json.dumps({'status':'PASS','migration_count':202,'b01_overlay_math_0153_unchanged':True,'judging':'NOT TESTED'},indent=2)+'\n')
  return
 if args.action=='logs':
  print(docker('event-log','logs',EVENT));return
 if args.action=='restart':
  docker('refresh-process-controller','cp',str(HERE/'b02_process.py'),SITE+':/tmp/b02_process.py')
  for mode in ['stop','start']:
   run('full-lifecycle-'+mode,['env','CPJ_SITE_REPORT_DIR='+str(OUT),sys.executable,'-B',str(HERE/'manage.py'),mode])
  return
 if args.action=='resolve':
  node=json.loads((ROOT/'reports/a09-site-1/base-pins.json').read_text())['node']
  print(docker('qu-published-versions','run','--rm',node,'npm','view','qu','versions','--json'));return
 if args.action=='setup':
  # Capture password hashes privately; bridge's native startup must be safe.
  shell('initial-state',"import json,os\nfrom pathlib import Path\nfrom django.contrib.auth.models import User\nfrom judge.models import Judge,Submission\nassert not Judge.objects.exists()\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\np=Path('/tmp/b02-passwords.json')\nif not p.exists():p.write_text(json.dumps(list(User.objects.order_by('pk').values_list('pk','password'))));p.chmod(0o600)\nprint('Preserved account hashes privately; no judges or in-progress submissions.')")
  work=WORK/'events';work.mkdir(exist_ok=True);shutil.copy2(HERE/'events/package.json',work/'package.json')
  lock=HERE/'events/package-lock.json'
  if lock.exists():shutil.copy2(lock,work/'package-lock.json')
  node=json.loads((ROOT/'reports/a09-site-1/base-pins.json').read_text())['node']
  command=('npm ci --ignore-scripts' if lock.exists() else 'npm install --package-lock-only --ignore-scripts && npm ci --ignore-scripts')
  docker('event-dependencies','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--mount',f'type=bind,src={work},dst=/work','--workdir','/work','--env','npm_config_cache=/tmp/npm',node,'sh','-c',command)
  if not lock.exists():shutil.copy2(work/'package-lock.json',lock)
  source=(ROOT/'build/a09-site-1/site/websocket/daemon.js').read_text()
  (work/'daemon.js').write_text(source.replace('followers.each(function','followers.array().forEach(function').replace('pollers.each(function','pollers.array().forEach(function'))
  (work/'config.js').write_text("module.exports={get_host:'0.0.0.0',get_port:9996,post_host:'0.0.0.0',post_port:9997,http_host:'0.0.0.0',http_port:9995,max_queue:50};\n")
  assert not exists()
  docker('event-create','run','-d','--name',EVENT,'--label','cpjudge.task=B02','--network','cpjudge-b01-web','--user',f'{os.getuid()}:{os.getgid()}','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','-p','127.0.0.1:9996:9996','-p','127.0.0.1:9995:9995','--mount',f'type=bind,src={work},dst=/work,readonly','--workdir','/work',node,'node','daemon.js')
  docker('event-private-network','network','connect','--alias','events','cpjudge-b01-net',EVENT)
  for name,target in [('b02_config.py','/app/dmoj/b02_config.py'),('b02_process.py','/tmp/b02_process.py')]:docker('install-'+name,'cp',str(HERE/name),SITE+':'+target)
  shell('enable-native-config',"from pathlib import Path\np=Path('/app/dmoj/local_settings.py');s=p.read_text();line=\"exec(open('/app/dmoj/b02_config.py').read())\"\nassert line not in s\np.write_text(s+'\\n# B02 native private services\\n'+line+'\\n')\n")
  # Reload only existing web process, retaining container and overlay.
  code="import os,signal\nfrom pathlib import Path\nfor p in Path('/proc').iterdir():\n if p.name.isdigit():\n  try:a=(p/'cmdline').read_bytes().split(bytes([0]))\n  except OSError:continue\n  if a[1:3]==[b'manage.py',b'runserver']:os.kill(int(p.name),signal.SIGTERM)\n"
  docker('reload-web','exec','-i',SITE,'python',input=code)
  docker('web-start','exec','-d',SITE,'sh','-c','exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/b02-http.log 2>&1')
  (WORK/'enabled').write_text('B02 lifecycle enabled\n')
 if args.action in ['setup','start']:
  guard=(HERE/'b03_guard.py').read_text() if (ROOT/'build/b03-worker-1/enabled').exists() else "from judge.models import Judge,Submission\nassert not Judge.objects.exists()\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nprint('Safe native bridge startup: no enrolled judges or in-progress submissions.')"
  shell('safe-bridge-start',guard)
  if exists() and not (ROOT/'build/phase-c-checkpoint1-1/enabled').exists():docker('event-start','start',EVENT)
  process('start')
  for _ in range(20):
   state=json.loads(process('status'))
   if state=={'bridge':1,'celery':1}:break
   time.sleep(1)
  else:raise RuntimeError('B02 services not ready within 20 seconds: bridge=%s celery=%s; inspect private process logs' % (state['bridge'],state['celery']))
  print(json.dumps(state));return
 if args.action=='stop':
  running=subprocess.check_output(['docker','inspect',SITE,'--format','{{.State.Running}}'],text=True).strip()=='true'
  if running and (ROOT/'build/b03-worker-1/enabled').exists():
   shell('safe-bridge-stop',(HERE/'b03_guard.py').read_text()+"\nassert not Judge.objects.filter(online=True).exists(), 'Stop the owned worker before bridge services'\n")
  if running:process('stop')
  if exists():docker('event-stop','stop',EVENT)
  return
 if args.action=='status':
  running=subprocess.check_output(['docker','inspect',SITE,'--format','{{.State.Running}}'],text=True).strip()=='true'
  state=json.loads(process('status')) if running else {'bridge':0,'celery':0}
  print(json.dumps(state))
  if running and state!={'bridge':1,'celery':1}:
   raise RuntimeError('B02 services unhealthy: bridge=%s celery=%s; inspect private process logs' % (state['bridge'],state['celery']))
  event_status=docker('event-status','inspect',EVENT,'--format','{{.State.Running}} {{json .NetworkSettings.Ports}}')
  print(event_status)
  if running:
   expected_event=not (ROOT/'build/phase-c-checkpoint1-1/enabled').exists()
   if (event_status.split()[0]=='true')!=expected_event:
    raise RuntimeError('B02 event service state disagrees with active polling mode; inspect private event log')
  return
 if args.action=='verify':
  output=shell('actual-service-probes',(HERE/'b02_probe.py').read_text());data=json.loads(output[output.index('{'):])
  shell('passwords-preserved',"import json\nfrom pathlib import Path\nfrom django.contrib.auth.models import User\nassert json.loads(Path('/tmp/b02-passwords.json').read_text())==[list(x) for x in User.objects.order_by('pk').values_list('pk','password')]\nprint('All existing password hashes unchanged.')")
  (OUT/('result-'+stamp+'.json')).write_text(json.dumps(data,indent=2)+'\n')
  return
 if args.action=='browser':
  output=WORK/'browser'/stamp;output.mkdir(parents=True)
  docker('website-login-browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--env','B01_URL=http://127.0.0.1:8000','--mount',f'type=bind,src={ROOT / "build/b01-site-1/private/accounts.json"},dst=/run/accounts.json,readonly','--mount',f'type=bind,src={HERE / "browser.py"},dst=/tests/browser.py,readonly','--mount',f'type=bind,src={output},dst=/results','cpjudge-b01-browser:local1','python','/tests/browser.py',private=True)
  data=json.loads((output/'result.json').read_text());(OUT/('browser-'+stamp+'.json')).write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
