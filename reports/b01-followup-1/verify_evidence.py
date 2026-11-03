"""Validate this follow-up's saved evidence, credentials exclusion and preservation."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
WORK=ROOT/'build/b01-followup-1'
def read(name):return json.loads((OUT/name).read_text())
before=json.loads((WORK/'before-files.json').read_text())
allowed={'AGENTS.md','PROJECT_STATUS.md','SecureExam-Implementation-Plan.md','patches/site/README.md',
         'deploy/site-local/manage.py','deploy/site-local/accounts.py','deploy/site-local/audit.py'}
changed=[]
for name,digest in before.items():
    p=ROOT/name;assert p.is_file(),('removed existing work',name)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changed.append(name)
assert set(changed)<=allowed,changed
runtime=read('runtime-final.json');assert runtime['status']=='PASS'
assert runtime['applied_migrations']==202 and runtime['autodetector_changes']=={}
assert runtime['temporary_fixtures_removed'] and runtime['host_login_http_status']==200
assert runtime['math_files_sha256']==read('math-assets.json')['files_sha256']
assert all(len(v)==1 for v in runtime['static_destinations'].values())
assert read('accounts-cleanup.json')['existing_users_profiles_identical']
assert read('accounts-cleanup.json')['domain_counts_unchanged']
checks={}
for phase in ['change','after-verify','after-reset','math-final']:
    path=sorted(OUT.glob('browser-'+phase+'-*.json'))[-1]
    data=json.loads(path.read_text());assert data['status']=='PASS' and data['page_error_count']==0
    checks[phase]=path.name
math=json.loads((OUT/checks['math-final']).read_text())
assert all(row['equations']==3 and not row['duplicate_equations'] for row in math['checks'].values())
assert math['checks']['statement']['color_extension_correct'] and math['checks']['preview']['color_extension_correct']
assert math['external_math_requests']==0
assert all(status==200 for status in math['local_math_assets'].values())
verification=json.loads(sorted(OUT.glob('verification-*.json'))[-1].read_text())
assert verification['password_hashes_unchanged'] and not verification['development_accounts_reset']
assert not verification['fixtures_loaded'] and not verification['migrations_applied']
secret_values=[]
for directory in [ROOT/'build/b01-site-1/private',WORK/'private']:
    for p in directory.glob('*.env'):
        secret_values.extend(line.split('=',1)[1] for line in p.read_text().splitlines() if '=' in line)
    for p in directory.glob('accounts*.json'):
        for row in json.loads(p.read_text()).values():
            secret_values.extend(v for v in row.values() if isinstance(v,str))
scanned=0
for parent in [OUT,ROOT/'deploy/site-local',ROOT/'patches/site',ROOT/'docs/contracts']:
    for path in parent.rglob('*'):
        if path.is_file():
            text=path.read_text()
            assert all(value not in text for value in secret_values if len(value)>=6),('credential leaked',str(path))
            scanned+=1
for path in [OUT/'README.md',ROOT/'PROJECT_STATUS.md',ROOT/'AGENTS.md',ROOT/'SecureExam-Implementation-Plan.md',ROOT/'docs/contracts/ui-direction.md']:
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if target.startswith(('https://','http://','#','mailto:')):continue
        dest=path.parent/target.split('#',1)[0]
        assert dest==OUT/'preservation.json' or dest.exists(),(str(path),target)
diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
assert diff.returncode==0,diff.stdout+diff.stderr
source=ROOT/'build/a09-site-1/site'
assert subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True).strip()==''
result={'status':'PASS','command':'python3 -B reports/b01-followup-1/verify_evidence.py','exit_status':0,
        'baseline_files_checked':len(before),'changed_existing_files':sorted(changed),
        'all_other_existing_files_byte_identical':True,'original_b01_a09_and_prior_reports_byte_identical':True,
        'source_checkout_clean':True,'credentials_found':False,'credential_scan_files':scanned,
        'authoritative_browser_reports':checks,'private_fixtures_removed':True,
        'ui_direction':'recorded; Foobar asset not invented; product home not implemented',
        'actual_problem_import_judging_standings':'NOT TESTED','commit_or_push':False,
        'git_diff_check_exit_status':diff.returncode}
(OUT/'preservation.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: follow-up browser/password/static/migration evidence, original reports/work preservation and credential exclusion.')
