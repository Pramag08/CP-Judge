"""Saved B04/B05 acceptance and preservation audit; no runtime mutations."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.site_problem import canonical_digest, file_manifest

OUT = Path(__file__).resolve().parent
B04 = ROOT / 'reports/b04-installation-1'
allowed = {'AGENTS.md', 'PROJECT_STATUS.md', 'SecureExam-Implementation-Plan.md',
           'README.md', 'MVP_DEPENDENCIES.md', 'deploy/site-local/problem_install.py'}
changed = set()
baselines = {}
for phase in ('b04-installation-1', 'b05-problem-1'):
    before = json.loads((ROOT / 'build' / phase / 'before.json').read_text())
    baselines[phase] = len(before)
    for name, sha in before.items():
        path = ROOT / name
        assert path.is_file(), name
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            assert name in allowed, name
            changed.add(name)
for directory in (B04, OUT):
    review = json.loads((directory / 'review.json').read_text())
    assert review['status'] == 'PASS' and review['blockers'] == []
    for name, sha in review['inspected_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    for row in json.loads((directory / 'commands.json').read_text()):
        assert (ROOT / row['log']).is_file(), row
installs = [json.loads(p.read_text()) for p in sorted(OUT.glob('installation-*.json'))]
assert len(installs) >= 2 and all(i['status'] == 'PASS' for i in installs)
assert installs[0]['directory_created'] and installs[0]['problem_created']
assert all(not i['directory_created'] and not i['problem_created'] for i in installs[1:])
assert len({(i['problem_pk'], i['native_code'], i['manifest_digest']) for i in installs}) == 1
verification = json.loads(sorted(OUT.glob('verification-*.json'))[-1].read_text())
assert verification['status'] == 'PASS'
assert verification['actual_worker']['input_output_pairs'] == 103
assert verification['actual_worker']['archive_entries'] == 206
assert verification['site_and_advertisement']['native_worker_recognizes_problem']
assert verification['site_and_advertisement']['submission_count'] == 0
assert verification['site_and_advertisement']['allowed_languages'] == ['CPP23']
assert verification['actual_worker']['time_seconds'] == 2.0 and verification['actual_worker']['memory_KiB'] == 262144
assert verification['source_verification']['statement_assets_verified'] == 15
assert verification['source_verification']['sample_tests_verified'] == 1
registry = json.loads((ROOT / 'build/b05-problem-1/private/registry.json').read_text())
assert canonical_digest(registry['manifest']) == registry['manifest_digest'] == installs[-1]['manifest_digest']
parent = ROOT / 'build/b03-worker-1/problems'
assert parent.stat().st_mode & 0o777 == 0o700
assert file_manifest(parent / installs[-1]['native_code']) == registry['manifest']['files']
privacy = json.loads(sorted(OUT.glob('privacy-*.json'))[-1].read_text())
assert privacy['status'] == 'PASS' and privacy['actual_http_roles_verified']
total = 0
for groups in privacy['responses'].values():
    for counts in groups.values():
        assert set(counts) <= {'302', '403', '404'}
        total += sum(counts.values())
assert total == 696
assert json.loads((OUT / 'source-route-coverage.json').read_text())['corrected_xml_xpath_targets_equal_tested_targets']
preservation = json.loads(sorted(OUT.glob('preserve-*.json'))[-1].read_text())
assert preservation['status'] == 'PASS' and preservation['preexisting_rows_match_recorded_snapshot']
assert preservation['datetime_snapshot_precision'] == 'milliseconds (DjangoJSONEncoder)'
assert sorted(preservation['only_new_rows'].values()) == [1, 1, 1, 1]
cleanup = json.loads(sorted(OUT.glob('session-cleanup-*.json'))[-1].read_text())
assert cleanup['status'] == 'PASS' and cleanup['database_and_cache_deleted'] and cleanup['owned_diagnostic_keys_cleared'] == 3
unit = json.loads((OUT / 'unit-tests.json').read_text())
assert unit['exit_status'] == 0 and unit['tests'] == 6 and (ROOT / unit['log']).is_file()
secrets = [json.loads((ROOT / 'build/b03-worker-1/private/worker.json').read_text())['key']]
for row in json.loads((ROOT / 'build/b01-site-1/private/accounts.json').read_text()).values():
    secrets.extend(row.values())
for path in (ROOT / 'build/b01-site-1/private').glob('*.env'):
    secrets.extend(line.split('=', 1)[1] for line in path.read_text().splitlines() if '=' in line)
for path in (ROOT / 'build/b05-problem-1/logs').glob('*/temporary-privacy-session.log'):
    text = path.read_text()
    if 'OPERATOR_RESULT=' in text:
        secrets.append(json.loads(text.split('OPERATOR_RESULT=', 1)[1])['key'])
before = json.loads((ROOT / 'build/b04-installation-1/before.json').read_text())
for path in ROOT.rglob('*'):
    if not path.is_file() or any(part in ('build', '.git', '.venv', '.deps', 'local-packages', 'node_modules', '__pycache__') for part in path.parts):
        continue
    name = str(path.relative_to(ROOT))
    if name in before and name not in changed:
        continue
    data = path.read_bytes()
    assert not any(str(secret).encode() in data for secret in secrets if len(str(secret)) >= 6), name
for name in ('local-packages/gaming-grid.zip', 'build/b05-problem-1/private/registry.json',
             'build/b03-worker-1/problems/' + installs[-1]['native_code']):
    assert subprocess.run(['git', 'check-ignore', '-q', name], cwd=ROOT).returncode == 0, name
for name in ('registry.json',):
    path = ROOT / 'build/b05-problem-1/private' / name
    assert path.stat().st_mode & 0o777 == 0o600
assert subprocess.run(['git', 'diff', '--check'], cwd=ROOT).returncode == 0
result = {'status': 'PASS', 'command': '.venv/bin/python -B reports/b05-problem-1/verify_evidence.py',
          'exit_status': 0, 'baseline_files': baselines, 'changed_existing_files': sorted(changed),
          'prior_reports_pins_accounts_passwords_worker_configuration_preserved': True,
          'snapshot_datetime_precision': 'milliseconds; diagnostic last_access restored to recorded precision',
          'public_credential_values_found': False, 'private_packages_registry_data_gitignored': True,
          'http_download_denials': total, 'unit_tests_passed': 6, 'independent_B04_B05_reviews': 'PASS',
          'git_diff_check_exit': 0, 'conversion': 'REUSED A02; independently verified, not rerun',
          'judging': 'NOT TESTED', 'B06': 'NOT STARTED'}
(OUT / 'evidence-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS: B04/B05 reviewed evidence, installed bytes, privacy, safe repeat and preservation.')
