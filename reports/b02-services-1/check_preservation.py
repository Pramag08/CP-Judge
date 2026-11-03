import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
before=json.loads((R/'build/b02-services-1/before.json').read_text())
allowed={'deploy/site-local/manage.py','AGENTS.md','PROJECT_STATUS.md','SecureExam-Implementation-Plan.md'}
changed=[]
for name,h in before.items():
 p=R/name;assert p.is_file(),name
 if hashlib.sha256(p.read_bytes()).hexdigest()!=h:changed.append(name)
assert set(changed)<=allowed,changed
results=sorted(O.glob('result-*.json'));assert len(results)>=3
for p in results:
 x=json.loads(p.read_text());assert x['status']=='PASS' and x['judges']==0
for p in O.glob('browser-*.json'):
 x=json.loads(p.read_text());assert x['status']=='PASS' and x['page_error_count']==0
assert json.loads((O/'review.json').read_text())['status']=='PASS'
assert json.loads((O/'runtime-preservation.json').read_text())['status']=='PASS'
secret=[]
for p in (R/'build/b01-site-1/private').glob('*.env'):secret.extend(s.split('=',1)[1] for s in p.read_text().splitlines() if '=' in s)
for row in json.loads((R/'build/b01-site-1/private/accounts.json').read_text()).values():secret.extend(row.values())
for p in O.rglob('*'):
 if p.is_file():assert all(v not in p.read_text() for v in secret if len(v)>=6),str(p)
check=subprocess.run(['git','diff','--check'],capture_output=True,text=True);assert check.returncode==0,check.stdout
(O/'preservation.json').write_text(json.dumps({'status':'PASS','command':'python3 -B reports/b02-services-1/check_preservation.py','exit_status':0,'baseline_files':len(before),'changed_existing_files':changed,'all_other_existing_files_and_prior_reports_byte_identical':True,'credentials_found':False,'judging':'NOT TESTED'},indent=2)+'\n')
print('PASS: prior work/reports preserved, service/browser/review evidence checked, credentials excluded.')
