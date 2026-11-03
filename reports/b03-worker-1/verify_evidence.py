"""Saved-evidence/preservation audit; no Docker, database or credentials output."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
before = json.loads((ROOT / 'build/b03-worker-1/before.json').read_text())
allowed = {'AGENTS.md', 'README.md', 'PROJECT_STATUS.md', 'SecureExam-Implementation-Plan.md',
           'MVP_DEPENDENCIES.md', 'deploy/site-local/b02.py', 'deploy/site-local/manage.py',
           'deploy/site-local/audit.py'}
changed = []
for name, sha in before.items():
    path = ROOT / name
    assert path.is_file(), name
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        assert name in allowed, name
        changed.append(name)

assert json.loads((OUT / 'acceptance.json').read_text())['status'] == 'PASS'
review = json.loads((OUT / 'review.json').read_text())
assert review['status'] == 'PASS'
for name, sha in review['inspected_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
cap = json.loads(sorted(OUT.glob('capabilities-*.json'))[-1].read_text())
assert cap['status'] == 'PASS' and len(cap['executors']) == 5
for key, row in cap['executors'].items():
    assert row['compiler_full_version'] == '16.2.0'
    assert row['sandbox_socket_denials'] == 6 and row['private_config_read_denied']
assert cap['executors']['CPP23']['cplusplus'] == 202302 and cap['executors']['CPP23']['CPP23_expected_feature']
states = [json.loads(p.read_text()) for p in sorted(OUT.glob('state-*.json'))]
assert states[-1]['online'] and states[-1]['native_website_status_matches'] and states[-1]['problems'] == 0
assert any(not s['online'] and not s['runtime_versions'] and s.get('worker_container_exit_code') == 0
           and s['worker_oom_killed'] is False and s['native_website_status_matches'] for s in states)
preserve = json.loads(sorted(OUT.glob('preservation-*.json'))[-1].read_text())
assert preserve['status'] == 'PASS' and preserve['all_preexisting_rows_exact'] and preserve['runtime_overlay_math_0153_exact']
assert preserve['new_languages'] == 0 and preserve['migrations'] == 202
sandbox = json.loads(sorted(OUT.glob('sandbox-*.json'))[-1].read_text())
assert sandbox['user'] == 'judge' and sandbox['read_only_root'] and sandbox['worker_api_disabled']
assert sandbox['network_mode'].startswith('container:') and sandbox['ports'] == {}
assert sandbox['cap_drop'] == ['ALL'] and sandbox['cap_add'] == ['CAP_SYS_PTRACE']
assert sandbox['security_opt'] == ['no-new-privileges'] and sandbox['pids_limit'] == 128
assert sandbox['memory'] == 2147483648 and sandbox['nano_cpus'] == 2000000000
assert sorted((m['destination'], m['read_only']) for m in sandbox['mounts']) == [('/config.yml', True), ('/problems', True)]
commands = json.loads((OUT / 'commands.json').read_text())
for row in commands:
    assert (ROOT / row['log']).is_file(), row
service_log = ROOT / [r for r in commands if r.get('name') == 'services-status'][-1]['log']
services = service_log.read_text()
assert all(name + '\tUp' in services for name in ('cpjudge-b01-site', 'cpjudge-b01-redis', 'cpjudge-b01-db'))
support_log = ROOT / [r for r in commands if r.get('name') == 'b02-status'][-1]['log']
support = support_log.read_text()
assert '"bridge": 1' in support and '"celery": 1' in support and 'true {' in support
verification = json.loads(sorted(OUT.glob('verification-*.json'))[-1].read_text())
assert verification['status'] == 'PASS' and verification['password_hashes_unchanged']
assert verification['judge_rows'] == 1 and verification['runtime_rows'] == 5
secrets = [json.loads((ROOT / 'build/b03-worker-1/private/worker.json').read_text())['key']]
for row in json.loads((ROOT / 'build/b01-site-1/private/accounts.json').read_text()).values():
    secrets.extend(row.values())
for path in (ROOT / 'build/b01-site-1/private').glob('*.env'):
    secrets.extend(line.split('=', 1)[1] for line in path.read_text().splitlines() if '=' in line)
private = ROOT / 'build/b03-worker-1/private'
assert private.stat().st_mode & 0o777 == 0o700
for name in ('worker.json', 'config.yml'):
    path = private / name
    assert path.stat().st_mode & 0o777 == 0o600
    assert subprocess.run(['git', 'check-ignore', '-q', str(path)], cwd=ROOT).returncode == 0
for path in ROOT.rglob('*'):
    if not path.is_file() or any(p in ('build', '.git', '.venv', '.deps', 'node_modules', 'local-packages', '__pycache__') for p in path.parts):
        continue
    name = str(path.relative_to(ROOT))
    if name in before and name not in changed:
        continue
    data = path.read_bytes()
    assert not any(value.encode() in data for value in secrets if len(value) >= 6), name
diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
assert diff.returncode == 0, diff.stdout
result = {'status': 'PASS', 'command': 'python3 -B reports/b03-worker-1/verify_evidence.py', 'exit_status': 0,
          'baseline_files': len(before), 'changed_existing_files': sorted(changed),
          'all_prior_reports_and_pins_byte_identical': True, 'credential_values_found': False,
          'private_file_permissions_and_ignore': 'PASS', 'git_diff_check_exit': 0,
          'ordinary_verify_passwords_preserved': True, 'all_required_services_running': True,
          'website_judging': 'NOT TESTED'}
(OUT / 'evidence-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS: B03 saved evidence, preserved data/files/pins and private credential exclusion.')
