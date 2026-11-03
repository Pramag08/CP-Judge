"""Own only the two native B02 processes inside the existing site container."""
import json,os,signal,subprocess,sys,time,fcntl
from pathlib import Path
specs={'bridge':['python','manage.py','runbridged'],
       'celery':['celery','-A','dmoj_celery','worker','--pool=solo','--concurrency=1','--prefetch-multiplier=1','-Q','celery,cpj_import','--loglevel=INFO','--hostname=b02@site']}
def matches(name):
 out=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   args=(p/'cmdline').read_bytes().decode().split('\0');stat=(p/'stat').read_text().split()[2]
  except OSError:continue
  if stat=='Z':continue
  if name=='bridge':match=args[1:3]==['manage.py','runbridged']
  else:match='--hostname=b02@site' in args and 'worker' in args
  if match:out.append(int(p.name))
 return out
lock=open('/tmp/b02-process.lock','a');fcntl.flock(lock,fcntl.LOCK_EX)
mode=sys.argv[1]
for name,command in specs.items():
 pids=matches(name);assert len(pids)<=1,(name,pids)
 if mode=='start' and not pids:
  fd=os.open('/tmp/b02-'+name+'.log',os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
  subprocess.Popen(command,cwd='/app',stdout=fd,stderr=fd,start_new_session=True);os.close(fd)
 if mode=='stop':
  for pid in pids:os.kill(pid,signal.SIGTERM)
  for _ in range(100):
   if not matches(name):break
   time.sleep(.1)
  assert not matches(name),name+' did not stop'
print(json.dumps({name:len(matches(name)) for name in specs}))
