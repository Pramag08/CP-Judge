"""Private development-fixture mapping and guarded email-only acceptance."""
import gzip,json,os,sys
from pathlib import Path
import c05 as d
ROOT,HERE,SITE=d.ROOT,d.HERE,d.SITE
WORK=ROOT/'build/phase-c-c18-cutover-1';OUT=ROOT/'reports/phase-c-c18-cutover-1'
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
  shell_file('c18_cutover_snapshot')
  d.docker('retain-private-baseline','cp',SITE+':/tmp/c18-cutover-before.json',str(WORK/'before.json'));(WORK/'before.json').chmod(0o600)
 elif action=='stage':d.docker('stage-provenance-and-tests','cp',str(HERE/'cpjudge')+'/.',SITE+':/app/cpjudge')
 elif action=='prepare-mappings':
  p=ROOT/'build/email-mappings-1/mappings.json'
  old=p.read_bytes();backup=WORK/'original-worksheet.json'
  with backup.open('xb') as f:os.chmod(backup,0o600);f.write(old)
  data=json.loads(old)
  private_assignments=json.loads((WORK/'authorized-development-addresses.json').read_text())
  assigned={int(pk):(row['username'],row['email']) for pk,row in private_assignments.items()}
  assert len(data['accounts'])==4
  for row in data['accounts']:
   name,email=assigned[row['user_id']];assert row['username']==name
   row.update(email=email,verified_by_organizer=False,assignment_kind='organizer_assigned_development',organizer_assigned=True,mailbox_verified=False,real_participant_identity=False,
              reason='User-authorized organizer assignment to existing development fixture on 2026-10-30; not a verified mailbox or real participant identity.')
  p.write_text(json.dumps(data,indent=2)+'\n');p.chmod(0o600)
  print('Four explicit user-assigned development mappings prepared privately; no verification claim or DB change.')
 elif action=='check-mappings':d.run('check-authorized-mappings',['python3','-B',str(HERE/'email_mappings.py'),'check'])
 elif action=='apply-mappings':d.run('apply-authorized-mappings',['python3','-B',str(HERE/'email_mappings.py'),'apply'])
 elif action=='tests':d.docker('focused-email-only-checks','exec','--user','1000:1000',SITE,'python','manage.py','test',*sys.argv[2:],'--settings=dmoj.cpj_integration_settings','--keepdb','--noinput','-v','2')
 elif action=='reload':
  import c13_bundle as old
  d.WORK,d.OUT=WORK,OUT;old.reload()
 elif action=='browser-credentials':
  folder=WORK/'browser';folder.mkdir(mode=0o700,exist_ok=True)
  sources=[json.loads((ROOT/'build/b01-site-1/private/accounts.json').read_text()),json.loads((ROOT/'build/b10-b11-contest-1/accounts.json').read_text())]
  candidates={}
  def collect(value):
   if isinstance(value,dict):
    if 'username' in value and 'password' in value:candidates[value['username']]=value
    for item in value.values():collect(item)
  for value in sources:collect(value)
  worksheet=json.loads((ROOT/'build/email-mappings-1/mappings.json').read_text())
  rows=[]
  baseline=json.loads((WORK/'before.json').read_text())
  for row in worksheet['accounts']:
   credential=candidates[row['username']]
   entry={'user_id':row['user_id'],'username':row['username'],'email':row['email'],'password':credential['password']}
   profile=next(p for p in baseline['judge.profile'] if p['user_id']==row['user_id'])
   subs=[v for v in baseline['judge.submission'] if v['user_id']==profile['id'] and v['status']=='D' and v['result']=='AC']
   if subs:entry['history_submission']=subs[0]['id']
   rows.append(entry)
  path=folder/'accounts.json';path.write_text(json.dumps(rows));path.chmod(0o600)
  print('Existing fixture credentials assembled privately; no password generation or change.')
 elif action=='browser':
  folder=WORK/'browser';assert (folder/'accounts.json').exists()
  d.docker('actual-cutover-browser-'+sys.argv[2],'run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--shm-size','512m','--cap-drop','ALL','--security-opt','no-new-privileges',
   '--mount',f'type=bind,src={folder},dst=/results',
   '--mount',f'type=bind,src={HERE/"c18_cutover_browser.py"},dst=/tests/browser.py,readonly',
   'cpjudge-b01-browser:local1','python','/tests/browser.py',sys.argv[2])
  save('browser-'+sys.argv[2]+'.json',json.loads((folder/('result-'+sys.argv[2]+'.json')).read_text()))
 elif action=='shell':shell_file(sys.argv[2])
 elif action=='finish':
  import hashlib,ast
  names=['email_identity.py','identity.py','views.py','sessions.py','native.py']
  expected={name:hashlib.sha256((HERE/'cpjudge'/name).read_bytes()).hexdigest() for name in names}
  raw=d.docker('deployed-final-identity-source','exec',SITE,'python','-c',"import hashlib,json;from pathlib import Path;print(json.dumps({n:hashlib.sha256((Path('/app/cpjudge')/n).read_bytes()).hexdigest() for n in "+repr(names)+"}))")
  assert json.loads(raw)==expected
  d.docker('schema-consistency','exec',SITE,'python','manage.py','makemigrations','--check','--dry-run')
  log=sorted(WORK.glob('*focused-email-only-checks.log'))[-1].read_text()
  assert 'Ran 15 tests' in log and '\nOK\n' in log and 'skipped=' not in log
  assert json.loads((OUT/'browser-before.json').read_text())['status']=='PASS'
  assert json.loads((OUT/'browser-after.json').read_text())['status']=='PASS'
  assert json.loads((OUT/'browser-admin-route.json').read_text())['status']=='PASS'
  for name in ('c18_cutover.py','c18_cutover_browser.py','email_mappings.py'):ast.parse((HERE/name).read_text())
  d.run('whitespace',['git','diff','--check'])
  save('checks.json',{'status':'PASS','focused_tests':15,'skips':0,'deployed_identity_source_sha256':expected,'schema_consistency':True,'no_live_schema_migration':True,
   'existing_mapping_workflow_check_apply_exit_zero':True,'actual_browser_before_and_after_cutover_passed':True,'local_admin_recovery_rehearsed_isolated':True,'password_changes_or_resets':0})
 else:raise SystemExit('Unknown cutover action')
