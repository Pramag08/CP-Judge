"""Sequential B10/B11 operator fixture and genuine native browser acceptance."""
import datetime,grp,hashlib,json,os,shlex,subprocess,sys,secrets
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
ACTION=sys.argv[1]; assert ACTION in ('setup','b10','ce','pair','after','standings','collect','install-scoring','checks','preserve')
if grp.getgrnam('docker').gr_gid not in [os.getgid(),*os.getgroups()]:
 os.execvp('sg',['sg','docker','-c',shlex.join([sys.executable,'-B',str(Path(__file__).resolve()),ACTION])])
WORK=ROOT/'build/b10-b11-contest-1';OUT=ROOT/'reports/b10-b11-contest-1'
WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
private=WORK/(ACTION+'-'+stamp);private.mkdir(mode=0o700)
SITE='cpjudge-b01-site';WORKER='cpjudge-b03-worker'

def run(name,argv,stdin=None):
 p=subprocess.run(argv,input=stdin,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 log=private/(name+'.log');log.write_text(p.stdout);log.chmod(0o600)
 f=OUT/'commands.json';rows=json.loads(f.read_text()) if f.exists() else []
 rows.append({'action':ACTION,'argv':argv,'exit_status':p.returncode,'log':str(log.relative_to(ROOT))});f.write_text(json.dumps(rows,indent=2)+'\n')
 print(name+': exit '+str(p.returncode),flush=True);assert p.returncode==0,log
 return p.stdout

def docker(name,*argv,**kw):return run(name,['docker',*argv],**kw)
def shell(name,code):
 value=docker(name,'exec','-i',SITE,'python','manage.py','shell',stdin=code)
 return json.loads(value.split('JOURNEY_RESULT=',1)[1])
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')

def configuration():
 from tools.site_problem import file_manifest
 data={}
 for name in (SITE,WORKER):
  obj=json.loads(docker('inspect-'+name,'inspect',name))[0]
  data[name]=hashlib.sha256(json.dumps({k:obj[k] for k in ('Image','Config','HostConfig','Mounts')},sort_keys=True).encode()).hexdigest()
  if name==WORKER:
   mount=next(m for m in obj['Mounts'] if m['Destination']=='/problems');assert not mount['RW']
   data['problem_files']=file_manifest(Path(mount['Source'])/'pv000000000000000001')
   data['worker_config_sha256']=hashlib.sha256((ROOT/'build/b03-worker-1/private/config.yml').read_bytes()).hexdigest() if (ROOT/'build/b03-worker-1/private/config.yml').exists() else None
 return data

if ACTION=='setup':
 assert not (WORK/'accounts.json').exists(),'Do not reseed temporary accounts'
 save('configuration-before.json',configuration())
 args="MODE='snapshot'\nALLOW_PRIOR=True\nSNAPSHOT_PATH='/tmp/b10-b11-before.json'\n"
 baseline=shell('snapshot',args+(HERE/'submission_state.py').read_text());save('snapshot.json',baseline)
 accounts={name:{'username':'b10tmp'+name,'password':secrets.token_urlsafe(24)} for name in ('a','b')}
 accounts['outsider']=json.loads((ROOT/'build/b01-site-1/private/accounts.json').read_text())['participant']
 (WORK/'accounts.json').write_text(json.dumps(accounts));(WORK/'accounts.json').chmod(0o600)
 result=shell('provision', 'ACCOUNTS='+repr({k:v for k,v in accounts.items() if k!='outsider'})+'\n'+(HERE/'contest_fixture.py').read_text())
 save('fixture.json',result);sys.exit(0)

if ACTION in ('b10','ce','pair','after','standings'):
 source=ROOT/'build/a03-judge-1/pipeline/problems/gaming-grid'
 tests={t['label']:t for t in yaml.safe_load((source/'init.yml').read_text())['tests']}
 wrong=[tests['wrong_answer']['cases'][i] for i in range(1,104)]
 config={'action':ACTION,'wrong_cases':wrong,'start':json.loads((OUT/'fixture.json').read_text())['start']}
 (private/'config.json').write_text(json.dumps(config))
 for label,text in [('wrong',(source/tests['wrong_answer']['source']).read_text()),('accepted',(source/tests['reference']['source']).read_text()),('ce','int main( {')]:
  (private/(label+'.cpp')).write_text(text)
 # Refuse duplicate judging; collection/standings can repeat without submitting.
 expected={'b10':0,'ce':2,'pair':3,'after':5}
 guard=shell('preflight',"import json\nfrom judge.models import Submission,Contest\nc=Contest.objects.get(key='b10b11local1')\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nprint('JOURNEY_RESULT='+json.dumps({'count':Submission.objects.filter(contest_object=c).count()}))")
 if ACTION in expected:assert guard['count']==expected[ACTION], 'Inspect receipts; never blindly repeat a POST'
 try:
  docker('browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={WORK/"accounts.json"},dst=/run/accounts.json,readonly',
   '--mount',f'type=bind,src={private},dst=/run/probes,readonly',
   '--mount',f'type=bind,src={private},dst=/results',
   '--mount',f'type=bind,src={HERE/"contest_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
 finally:
  if (private/'receipts.json').exists():save(ACTION+'-receipts.json',json.loads((private/'receipts.json').read_text()))
  if (private/'sessions.json').exists():
   keys=json.loads((private/'sessions.json').read_text())
   shell('cleanup-owned-sessions','KEYS='+repr(keys)+"\nimport importlib,json\nfrom django.conf import settings\nb=importlib.import_module(settings.SESSION_ENGINE)\nfor key in KEYS:\n s=b.SessionStore(session_key=key);s.delete();assert s.load()=={}\nprint('JOURNEY_RESULT='+json.dumps({'deleted':len(KEYS)}))")
 result=json.loads((private/'browser.json').read_text());result['raw_evidence']=str(private.relative_to(ROOT));save(ACTION+'-browser-'+stamp+'.json',result)
 sys.exit(0)

if ACTION=='collect':
 result=shell('stored-receipts-and-standings',(HERE/'contest_results.py').read_text())
 trace=[json.loads(l) for l in docker('passive-trace','exec',SITE,'cat','/tmp/b07-native-trace.jsonl').splitlines()]
 ids={s['id'] for s in result['submissions']};trace=[r for r in trace if r.get('submission-id') in ids]
 for s in result['submissions']:
  rows=[r for r in trace if r['submission-id']==s['id']]
  req=[r for r in rows if r['name']=='submission-request'];assert len(req)==1
  assert req[0]['time-limit']==2 and req[0]['memory-limit']==262144 and req[0]['short-circuit'] is False
  assert req[0]['source_sha256']==s['source_sha256'] and req[0]['language']=='CPP23'
  cases=sorted([c for row in rows for c in row.get('cases',[])],key=lambda c:c['position']);assert len(cases)==s['case_count']
  assert [c['position'] for c in cases]==list(range(1,len(cases)+1))
  def native_status(flags):return next((name for bit,name in ((4,'TLE'),(8,'MLE'),(64,'OLE'),(2,'RTE'),(16,'IR'),(1,'WA'),(32,'SC')) if flags&bit),'AC')
  assert [native_status(c['status']) for c in cases]==s['case_statuses']
  assert sum(c['points'] for c in cases)==s['case_points']
  assert any(r['name']==('compile-error' if s['verdict']=='CE' else 'grading-end') for r in rows)
  assert s['judged_on'] is not None
 result['trace']=trace
 if result['format']=='cpjudge_icpc_v1':
  assert result['standings_match']
  latest=max(OUT.glob('*-browser-*.json'),key=lambda p:p.stat().st_mtime)
  browser=json.loads(latest.read_text())['standings']
  expected=[]
  for row in result['manual_expected']:
   seconds=row['penalty_seconds'];display=f'{seconds//3600:02}:{seconds%3600//60:02}:{seconds%60:02}'
   expected.append({'username':row['username'],'rank':row['rank'],'solved':row['solved'],'penalty_display':display})
  assert [{k:r[k] for k in expected[0]} for r in browser]==expected,(browser,expected)
  result['browser_matches_manual_expected']=True
  result['compared_browser_evidence']=str(latest.relative_to(ROOT))
 save('results-'+stamp+'.json',result);sys.exit(0)
if ACTION=='install-scoring':
 exec((HERE/'contest_scoring_install.py').read_text());sys.exit(0)
if ACTION=='checks':
 save('scoring-checks.json',shell('focused-scoring-checks',(HERE/'contest_scoring_checks.py').read_text()));sys.exit(0)
if ACTION=='preserve':
 assert configuration()==json.loads((OUT/'configuration-before.json').read_text())
 save('preserve.json',shell('preserve-existing-data',(HERE/'contest_preserve.py').read_text()));sys.exit(0)
