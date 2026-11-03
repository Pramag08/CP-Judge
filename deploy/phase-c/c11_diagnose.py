"""Private readiness diagnostic, no submission/worker configuration writes."""
import json
import c11 as env
from c11 import d, SITE, WORKER, OUT


def run():
    raw=d.docker('inspect-native-worker-socket','exec',WORKER,'/env/bin/python3','-c',"""import json,os
from pathlib import Path
inodes={}
for p in Path('/proc/1/fd').iterdir():
 try:inodes[os.readlink(p)]=p.name
 except OSError:pass
ports=[]
for line in Path('/proc/net/tcp').read_text().splitlines()[1:]:
 c=line.split()
 if int(c[2].split(':')[1],16)==9999 and c[3]=='01':ports.append({'port':int(c[1].split(':')[1],16),'owned':('socket:['+c[9]+']') in inodes})
print('C11_SOCKET='+json.dumps({'argv':Path('/proc/1/cmdline').read_bytes().decode().split(chr(0)),'ports':ports}))
""")
    socket=json.loads(raw.decode().split('C11_SOCKET=',1)[1].splitlines()[0])
    port=next(row['port'] for row in socket['ports'] if row['owned'])
    raw=d.shell('isolated-coordinator-readiness-diagnostic','PORT='+str(port)+'\n'+"""import json,hashlib,secrets,threading,time,traceback
from pathlib import Path
from types import SimpleNamespace
from cpjudge import bridge_readiness as g,readiness_wire as w
from judge.models import Judge,Problem,LanguageLimit,ProblemData
config=json.loads(g.CONFIG.read_text());p=Problem.objects.get(code='pv000000000000000001');j=Judge.objects.get(name='cpjudge-local-worker')
values={'actual_fields':{k:getattr(p,k) for k in ('time_limit','memory_limit','short_circuit','points','partial','is_manually_managed')},
 'actual_languages':list(p.allowed_languages.values_list('key',flat=True)),'language_limits':LanguageLimit.objects.filter(problem=p).count(),
 'problem_data':ProblemData.objects.filter(problem=p).count(),'worker_online':j.online,'worker_blocked':j.is_blocked,'worker_disabled':j.is_disabled}
try:
 conf,requirement,fields=g.requirements(p.code,'CPP23')
 values['requirements']='PASS'
 body={'schema':1,**requirement,'inventory':config['inventory'],'connection':secrets.token_hex(32),'peer_port':PORT,'nonce':secrets.token_hex(32),'issued':time.time()}
 reply=w.request(body,j.auth_key)
 values['signed_worker_ok']=reply.get('ok')
 Path('/tmp/c11-debug-body.json').write_text(json.dumps(body));Path('/tmp/c11-debug-body.json').chmod(0o600)
except Exception as e:values['error']=type(e).__name__+': '+str(e)
print('C11_DIAGNOSTIC='+json.dumps(values))
""")
    values=json.loads(raw.decode().split('C11_DIAGNOSTIC=',1)[1].splitlines()[0])
    values['native_socket_owned']=True
    print(json.dumps(values))
    raw=d.docker('copy-private-readiness-diagnostic','cp',SITE+':/tmp/c11-debug-body.json',str(env.WORK/'debug-body.json'))
    body=json.loads((env.WORK/'debug-body.json').read_text())
    body['issued']=__import__('time').time()
    raw=d.docker('worker-local-deep-diagnostic','exec','-i',WORKER,'/bin/bash','-c',
        '. ~judge/.profile; export HOME=/tmp; exec /env/bin/python3 -',data=("import sys,json,traceback\nsys.path.insert(0,'/tmp')\nimport c11_worker as s\nbody="+repr(body)+"\ntry:\n native=s.load_native();baseline=s.inventory(native);result=s.verify(body,native,baseline);print('C11_DEEP=PASS')\nexcept Exception:\n traceback.print_exc()\n").encode())
    print(raw.decode()[-1500:])
