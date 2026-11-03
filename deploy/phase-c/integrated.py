"""Same-version private contest acceptance and local email mapping preparation."""
import gzip,json,os,sys
from pathlib import Path
import c05 as d
ROOT,HERE,SITE=d.ROOT,d.HERE,d.SITE
WORK=ROOT/'build/phase-c-integrated-1';OUT=ROOT/'reports/phase-c-integrated-1'
WORK.mkdir(mode=0o700,parents=True,exist_ok=True);WORK.chmod(0o700);OUT.mkdir(parents=True,exist_ok=True)
d.WORK,d.OUT=WORK,OUT

def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def shell_file(name):return d.shell(name,(HERE/(name+'.py')).read_text())

if __name__=='__main__':
 action=sys.argv[1]
 if action=='snapshot':
  assert not (WORK/'database.sql.gz').exists()
  raw=d.docker('fresh-private-backup','exec','cpjudge-b01-db','sh','-c','exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01')
  p=WORK/'database.sql.gz'
  with p.open('xb') as f:os.chmod(p,0o600);f.write(gzip.compress(raw))
  assert gzip.decompress(p.read_bytes())==raw and b'-- Dump completed on' in raw
  shell_file('integrated_snapshot')
  d.docker('save-private-baseline','cp',SITE+':/tmp/integrated-before.json',str(WORK/'before.json'));(WORK/'before.json').chmod(0o600)
 elif action=='stage':
  d.docker('stage-current-app','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
 elif action=='migrate':
  assert (WORK/'before.json').exists()
  d.docker('generate-admission-migration','exec','--user','1000:1000',SITE,'python','manage.py','makemigrations','cpjudge','--noinput')
  d.docker('retain-admission-migration','cp',SITE+':/app/cpjudge/migrations/.',str(HERE/'cpjudge/migrations'))
  d.docker('apply-additive-migration','exec',SITE,'python','manage.py','migrate','--noinput')
 elif action=='reload':
  import c13_bundle as old
  d.WORK,d.OUT=WORK,OUT
  old.reload()
 elif action=='bridge-reload':
  import c11
  d.WORK,d.OUT=WORK,OUT
  d.shell('guard-idle-bridge-reload',"from judge.models import Submission\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()")
  d.run('stop-idle-worker',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'stop'])
  d.docker('stop-idle-bridge','exec','-i',SITE,'python','-c',c11.BRIDGE_STOP)
  d.docker('start-bridge','exec','-d',SITE,'sh','-c','exec python manage.py runbridged >> /tmp/b02-bridge.log 2>&1')
  import time;time.sleep(2)
  d.run('start-worker-verifier',['python3','-B',str(ROOT/'deploy/site-local/b03.py'),'start'])
 elif action=='tests':
  d.docker('focused-integration-admission-tests','exec','--user','1000:1000',SITE,'python','manage.py','test',*sys.argv[2:],'--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='shell':shell_file(sys.argv[2])
 elif action=='browser':
  folder=WORK/'browser';folder.mkdir(mode=0o700,exist_ok=True)
  d.docker('private-fixture-metadata','cp',SITE+':/tmp/integrated-fixture.json',str(folder/'fixture.json'));(folder/'fixture.json').chmod(0o600)
  for name in ('accepted.cpp','wrong.cpp'):
   path=folder/name
   if not path.exists():
    d.docker('private-known-'+name,'cp',SITE+':/tmp/integrated-'+name,str(path));path.chmod(0o600)
  accounts=json.loads((ROOT/'build/phase-c-checkpoint1-1/accounts.json').read_text())
  baseline=json.loads((WORK/'before.json').read_text())
  user=next(u for u in baseline['auth.user'] if u['username']==accounts['accounts']['q']['username'])
  identity=next(i for i in baseline['cpjudge.identity'] if i['user_id']==user['id'])
  accounts['accounts']['q']['login']=identity['canonical_email']
  private_accounts=folder/'accounts.json';private_accounts.write_text(json.dumps(accounts));private_accounts.chmod(0o600)
  d.docker('actual-same-version-browser-worker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={private_accounts},dst=/run/accounts.json,readonly',
   '--mount',f'type=bind,src={HERE/"integrated_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py')
  save('browser.json',json.loads((folder/'result.json').read_text()))
 elif action=='finish':
  import hashlib,ast
  from lxml import html
  proof=json.loads((OUT/'proof.json').read_text());browser=json.loads((OUT/'browser.json').read_text())
  assert [r['id'] for r in browser['runs']]==[r['id'] for r in proof['runs']]
  for owner in ('p','q'):
   doc=html.fromstring((WORK/'browser'/(owner+'-standings.html')).read_text())
   rows=[]
   for row in doc.xpath('//table[@id="ranking-table"]/tbody/tr'):
    username=row.get('id').removeprefix('user-');tds=row.xpath('./td')
    rank=int(tds[0].text_content().strip())
    score=int(row.xpath('./td[contains(@class,"user-points")]/a/text()')[0].strip())
    text=row.xpath('./td[contains(@class,"user-points")]//div[contains(@class,"solving-time")]/text()')[0].strip()
    h,m,sec=map(int,text.split(':'));penalty=h*3600+m*60+sec
    expected=proof['expected'][username]
    assert score==expected['solved'] and penalty==expected['penalty']
    rows.append({'rank':rank,'username':username,'solved':score,'penalty':penalty})
   assert rows==proof['native_ranks']
  names=['models.py','admission.py','native.py','publication.py','bridge_readiness.py']
  expected={n:hashlib.sha256((HERE/'cpjudge'/n).read_bytes()).hexdigest() for n in names}
  raw=d.docker('deployed-admission-source-check','exec',SITE,'python','-c',"import hashlib,json;from pathlib import Path;print(json.dumps({n:hashlib.sha256((Path('/app/cpjudge')/n).read_bytes()).hexdigest() for n in "+repr(names)+"}))")
  assert json.loads(raw)==expected
  d.docker('migration-consistency','exec',SITE,'python','manage.py','makemigrations','--check','--dry-run')
  final=sorted(WORK.glob('*focused-integration-admission-tests.log'))[-1].read_text()
  assert 'Ran 9 tests' in final and '\nOK\n' in final and 'skipped=' not in final
  for p in HERE.glob('integrated*.py'):ast.parse(p.read_text())
  ast.parse((HERE/'email_mappings.py').read_text())
  d.run('final-whitespace',['git','diff','--check'])
  save('checks.json',{'status':'PASS','final_focused_tests':9,'skips':0,'earlier_4_admission_plus_27_C11_regressions_passed':True,'both_browser_standings_equal_manual_and_SQL':True,
    'deployed_source_sha256':expected,'migration_consistency':True,'phase_c_complete':False,'email_only_cutover':'BLOCKED; four original blank addresses'})
 else:raise SystemExit('Unknown action')
