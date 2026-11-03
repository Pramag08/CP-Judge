"""B12 supported idle stop/start, persistence and one real native browser submission."""
import datetime,grp,hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
ACTION=sys.argv[1];assert ACTION in ('snapshot','stop','start','after','submit','final')
if grp.getgrnam('docker').gr_gid not in [os.getgid(),*os.getgroups()]:
 os.execvp('sg',['sg','docker','-c',shlex.join([sys.executable,'-B',str(Path(__file__).resolve()),ACTION])])
WORK=ROOT/'build/b12-restart-1';OUT=ROOT/'reports/b12-restart-1'
WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');private=WORK/(ACTION+'-'+stamp);private.mkdir(mode=0o700)
SITE='cpjudge-b01-site';WORKER='cpjudge-b03-worker'
NAMES=(SITE,'cpjudge-b01-db','cpjudge-b01-redis',WORKER,'cpjudge-b02-events')
os.environ['CPJ_SITE_REPORT_DIR']=str(OUT)
def run(name,argv,stdin=None):
 p=subprocess.run(argv,input=stdin,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 raw=private/(name+'.log');raw.write_text(p.stdout);raw.chmod(0o600)
 f=OUT/'commands.json';rows=json.loads(f.read_text()) if f.exists() else []
 rows.append({'action':ACTION,'argv':argv,'exit_status':p.returncode,'private_log':str(raw.relative_to(ROOT))});f.write_text(json.dumps(rows,indent=2)+'\n')
 print(name+': exit '+str(p.returncode),flush=True);assert p.returncode==0,raw
 return p.stdout

def docker(name,*argv,**kw):return run(name,['docker',*argv],**kw)
def shell(name,code):return json.loads(docker(name,'exec','-i',SITE,'python','manage.py','shell',stdin=code).split('JOURNEY_RESULT=',1)[1])
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def containers():
 data={}
 for name in NAMES:
  obj=json.loads(docker('inspect-'+name,'inspect',name))[0]
  data[name]={'id':obj['Id'],'image':obj['Image'],'running':obj['State']['Running'],'started':obj['State']['StartedAt'],
      'exit_code':obj['State']['ExitCode'],'oom':obj['State']['OOMKilled'],
      'configuration_sha256':hashlib.sha256(json.dumps({k:obj[k] for k in ('Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest(),
      'named_volumes':[m['Name'] for m in obj['Mounts'] if m['Type']=='volume']}
  if name==WORKER:
   from tools.site_problem import file_manifest
   mount=next(m for m in obj['Mounts'] if m['Destination']=='/problems');assert not mount['RW']
   data[name]['immutable_files']=file_manifest(Path(mount['Source'])/'pv000000000000000001')
   cfg=next(m for m in obj['Mounts'] if m['Destination']=='/config.yml');assert not cfg['RW']
   data[name]['worker_config_sha256']=hashlib.sha256(Path(cfg['Source']).read_bytes()).hexdigest()
 return data

def online():
 return shell('native-worker-readiness',"import json\nfrom judge.models import Judge,Submission\nj=Judge.objects.get(name='cpjudge-local-worker')\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nassert j.online and j.problems.filter(code='pv000000000000000001').exists()\nkeys=list(j.runtimes.order_by('key').values_list('key',flat=True));assert keys==['CPP11','CPP14','CPP17','CPP20','CPP23']\nprint('JOURNEY_RESULT='+json.dumps({'online':j.online,'executors':keys,'start_time':j.start_time.isoformat(),'installed_problem_advertised':True}))")

def server_results(tag):
 result=shell('record-'+tag,(HERE/'contest_results.py').read_text());assert result['standings_match'];save(tag+'-results.json',result);return result

def browser(action):
 output=private/'browser';output.mkdir()
 accounts={k:v for k,v in json.loads((ROOT/'build/b10-b11-contest-1/accounts.json').read_text()).items() if k in ('a','b')}
 accounts.update(json.loads((ROOT/'build/b01-site-1/private/accounts.json').read_text()))
 (private/'accounts.json').write_text(json.dumps(accounts));(private/'accounts.json').chmod(0o600)
 (output/'config.json').write_text(json.dumps({'action':action}))
 if action=='restart-submit':
  source=ROOT/'build/a03-judge-1/pipeline/problems/gaming-grid/solutions/reference.cpp'
  (output/'accepted.cpp').write_bytes(source.read_bytes())
 try:
  docker('browser-'+action,'run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={private/"accounts.json"},dst=/run/accounts.json,readonly',
   '--mount',f'type=bind,src={output},dst=/run/probes,readonly',
   '--mount',f'type=bind,src={output},dst=/results',
   '--mount',f'type=bind,src={HERE/"contest_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
 finally:
  if (output/'receipts.json').exists():save('new-receipt.json',json.loads((output/'receipts.json').read_text()))
  if (output/'sessions.json').exists():
   keys=json.loads((output/'sessions.json').read_text())
   shell('cleanup-owned-browser-sessions','KEYS='+repr(keys)+"\nimport json,importlib\nfrom django.conf import settings\nb=importlib.import_module(settings.SESSION_ENGINE)\nfor key in KEYS:\n s=b.SessionStore(session_key=key);s.delete();assert s.load()=={}\nprint('JOURNEY_RESULT='+json.dumps({'deleted':len(KEYS)}))")
 data=json.loads((output/'browser.json').read_text());data['private_evidence']=str(output.relative_to(ROOT));save(ACTION+'-browser.json',data);return data

if ACTION=='snapshot':
 assert not (OUT/'before-results.json').exists()
 state=containers();assert all(row['running'] for row in state.values());save('before-containers.json',state)
 save('before-worker.json',online())
 browser('persistence')
 save('snapshot.json',shell('snapshot-existing-rows',"MODE='snapshot'\nALLOW_PRIOR=True\nSNAPSHOT_PATH='/tmp/b12-before.json'\n"+(HERE/'submission_state.py').read_text()))
 docker('private-baseline-copy','cp',SITE+':/tmp/b12-before.json',str(WORK/'before-rows.json'));(WORK/'before-rows.json').chmod(0o600)
 server_results('before')
elif ACTION=='stop':
 assert (OUT/'snapshot.json').exists() and not (OUT/'stopped-containers.json').exists()
 online()
 run('supported-stop',[sys.executable,'-B',str(HERE/'manage.py'),'stop'])
 state=containers();assert not any(row['running'] for row in state.values())
 assert state[WORKER]['exit_code']==0 and not state[WORKER]['oom'];save('stopped-containers.json',state)
elif ACTION=='start':
 assert (OUT/'stopped-containers.json').exists()
 run('supported-start',[sys.executable,'-B',str(HERE/'manage.py'),'start'])
 state=containers();assert all(row['running'] for row in state.values())
 before=json.loads((OUT/'before-containers.json').read_text())
 for name,row in state.items():
  assert row['id']==before[name]['id'] and row['started']!=before[name]['started']
  for key in ('image','configuration_sha256','named_volumes','immutable_files','worker_config_sha256'):
   if key in row:assert row[key]==before[name][key],(name,key)
 save('restarted-containers.json',state);worker=online()
 assert worker['start_time']!=json.loads((OUT/'before-worker.json').read_text())['start_time'];save('reconnected-worker.json',worker)
elif ACTION=='after':
 result=server_results('after');assert result==json.loads((OUT/'before-results.json').read_text())
 save('restarted-preservation.json',shell('exact-persistence-compare',"MODE='restarted'\n"+(HERE/'restart_state.py').read_text()))
 actual=browser('persistence');before=json.loads((OUT/'snapshot-browser.json').read_text())
 assert actual['standings']==before['standings'] and actual['authenticated_account_roles']==before['authenticated_account_roles']
 save('after-acceptance.json',{'status':'PASS','server_results_exact_match':True,'browser_standings_exact_match':True,'all_existing_credential_roles_authenticated':actual['authenticated_account_roles']})
elif ACTION=='submit':
 before=json.loads((OUT/'before-results.json').read_text());current=server_results('pre-submit')
 assert current==before and (OUT/'after-acceptance.json').exists() and not (OUT/'new-receipt.json').exists()
 online();browser('restart-submit')
elif ACTION=='final':
 final=server_results('final');before=json.loads((OUT/'before-results.json').read_text());receipt=json.loads((OUT/'new-receipt.json').read_text());assert len(receipt)==1
 sid=receipt[0]['id'];subs=final['submissions'];new=[s for s in subs if s['id']==sid];assert len(new)==1
 assert [s for s in subs if s['id']!=sid]==before['submissions']
 assert final['actual']==before['actual'] and final['manual_expected']==before['manual_expected']
 s=new[0];assert s['status']=='D' and s['verdict']=='AC' and s['case_statuses']==['AC']*103 and s['contest_points']==1
 trace=[json.loads(line) for line in docker('passive-trace','exec',SITE,'cat','/tmp/b07-native-trace.jsonl').splitlines()]
 trace=[r for r in trace if r.get('submission-id')==sid];req=[r for r in trace if r['name']=='submission-request'];assert len(req)==1
 assert req[0]['language']=='CPP23' and req[0]['time-limit']==2 and req[0]['memory-limit']==262144 and req[0]['short-circuit'] is False
 assert req[0]['source_sha256']==s['source_sha256']
 cases=sorted([c for r in trace for c in r.get('cases',[])],key=lambda c:c['position']);assert len(cases)==103
 assert [c['position'] for c in cases]==list(range(1,104)) and all(c['status']==0 and c['points']==c['total-points']==1 for c in cases)
 assert any(r['name']=='grading-end' for r in trace)
 display=json.loads((OUT/'submit-browser.json').read_text());assert display['completed_case_count']==103 and display['displayed_verdict']=='AC' and len(display['posts'])==1
 assert display['posts'][0]['source_sha256']==s['source_sha256']
 assert display['standings']==json.loads((OUT/'after-browser.json').read_text())['standings']
 # Exact native row comparison includes all old source/case/result fields.
 save('final-preservation.json',shell('preserve-with-one-native-addition',"MODE='final'\n"+(HERE/'restart_state.py').read_text()))
 raw=docker('private-worker-log','logs',WORKER);lines=raw.splitlines()
 a=next(i for i,l in enumerate(lines) if f'Start grading pv000000000000000001/{sid} in CPP23' in l)
 b=next(i for i,l in enumerate(lines[a:],a) if f'Done grading pv000000000000000001/{sid}.' in l)
 import re
 worker_cases=[(int(m.group(1)),m.group(2)) for l in lines[a:b+1] if (m:=re.search(r'Test case\s+(\d+)\s+([A-Z]+)\s+\[',l))]
 assert worker_cases==[(i,'AC') for i in range(1,104)]
 save('new-native-trace.json',trace)
 state=containers();base=json.loads((OUT/'before-containers.json').read_text())
 for name,row in state.items():
  for key in ('id','image','configuration_sha256','named_volumes','immutable_files','worker_config_sha256'):
   if key in row:assert row[key]==base[name][key],(name,key)
 save('final-containers.json',state)
 save('acceptance.json',{'status':'PASS','new_submission_id':sid,'executed_AC_cases':103,'worker_stored_browser_agree':True,
  'standings_recomputed_correctly':'post-AC attempt adds no new solve or penalty; both 1 solved/2161 seconds/shared rank1',
  'old_results_persisted':True,'credentials_work':True,'worker_reconnected':True,'data_config_and_sandbox_preserved':True,
  'interrupted_submission_recovery':'NOT TESTED: graceful stop with no in-progress work'})
