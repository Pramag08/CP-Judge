"""Validate saved B01 acceptance evidence/preservation; does not rerun the stack."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
WORK=ROOT/'build/b01-site-1'
baseline=json.loads((OUT/'baseline.json').read_text())
assert baseline['applied_migrations']==202 and baseline['new_migration_applied']
assert baseline['autodetector_changes']=={}
assert baseline['changed_zoneinfo_inventory_does_not_create_migration']
assert baseline['website_dependency_lock_unchanged']
assert baseline['judge_rows']==baseline['runtime_rows']==0
assert baseline['judge_connection']=='NOT TESTED' and baseline['b02_started'] is False
browser_reports=sorted(OUT.glob('browser-[0-9]*.json'))
assert browser_reports, 'no actual browser result'
browser=json.loads(browser_reports[-1].read_text())
assert browser['status']=='PASS' and browser['chromium_version']
assert len(browser['checks'])>=8
assert browser['website_to_judge']=='NOT TESTED'
review=json.loads((OUT/'review.json').read_text())
assert review['status']=='PASS',review
for filename, expected in review['inspected_sha256'].items():
    assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==expected, ('changed after independent review',filename)
previous=json.loads((WORK/'before-files.json').read_text())
changed=[]
for name,digest in previous.items():
    p=ROOT/name
    assert p.is_file(),('removed existing file',name)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changed.append(name)
assert set(changed)<= {'PROJECT_STATUS.md','SecureExam-Implementation-Plan.md','AGENTS.md'}
credentials=json.loads((WORK/'private/accounts.json').read_text())
secrets=[v for data in credentials.values() for v in data.values()]
for path in (WORK/'private').glob('*.env'):
    secrets.extend(line.split('=',1)[1] for line in path.read_text().splitlines() if '=' in line)
scanned=0
for parent in [OUT,ROOT/'deploy/site-local',ROOT/'patches/site']:
    for path in parent.rglob('*'):
        if path.is_file():
            text=path.read_text()
            assert all(value not in text for value in secrets if len(value)>=6),('credential leak',str(path))
            scanned+=1
for path in [OUT/'README.md',ROOT/'PROJECT_STATUS.md',ROOT/'SecureExam-Implementation-Plan.md']:
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if target.startswith(('https://','http://','#','mailto:')):continue
        assert (path.parent/target.split('#',1)[0]).exists(),(str(path),target)
diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
assert diff.returncode==0,diff.stdout+diff.stderr
result={'status':'PASS','command':'python3 -B reports/b01-site-1/verify_evidence.py','exit_status':0,
        'baseline_files_checked':len(previous),'changed_existing_files':sorted(changed),
        'all_other_previous_files_byte_identical':True,'files_scanned_for_private_credentials':scanned,
        'credentials_found':False,'independent_review':'PASS','reviewed_source_and_evidence_hashes_still_match':True,'actual_browser_report':browser_reports[-1].name,
        'git_diff_check_exit_status':diff.returncode,'website_to_judge':'NOT TESTED','b02_started':False}
(OUT/'preservation.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: B01 saved browser/migration/review evidence, prior work preservation and credential exclusion.')
