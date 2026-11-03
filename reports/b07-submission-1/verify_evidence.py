"""Audit saved B06/B07 evidence; never submit, rejudge or mutate the database."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.site_problem import file_manifest, canonical_digest

OUT = Path(__file__).resolve().parent
B06 = ROOT / 'reports/b06-statement-1'
allowed = {'AGENTS.md', 'PROJECT_STATUS.md', 'SecureExam-Implementation-Plan.md', 'README.md',
           'MVP_DEPENDENCIES.md', 'patches/site/README.md', 'deploy/site-local/problem_install.py',
           'deploy/site-local/problem_models.py', 'deploy/site-local/problem_journey.py'}
changes, counts = set(), {}
for phase in ('b06-statement-1', 'b07-submission-1'):
    baseline = json.loads((ROOT / 'build' / phase / 'before.json').read_text())
    counts[phase] = len(baseline)
    for name, sha in baseline.items():
        path = ROOT / name
        assert path.is_file(), name
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            assert name in allowed, name
            changes.add(name)
for directory in (B06, OUT):
    review = json.loads((directory / 'review.json').read_text())
    assert review['status'] == 'PASS' and review['blockers'] == []
    for name, sha in review['inspected_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    for command in json.loads((directory / 'commands.json').read_text()):
        assert (ROOT / command['log']).is_file()
render = json.loads(sorted(B06.glob('browser-*.json'))[-1].read_text())
assert render['status'] == 'PASS' and render['math_expressions'] == 30 and render['math_source_exact_order_match']
assert all(render['source_sections_and_samples_match'].values())
assert render['page_error_count'] == 0 and render['private_data_route_denials'] == 219
assert render['anonymous_problem_css_denied'] and render['scoped_css_authenticated']
assert all(value == 200 for value in render['local_assets'].values())
assert json.loads(sorted(B06.glob('preservation-*.json'))[-1].read_text())['status'] == 'PASS'
browser = json.loads(sorted(OUT.glob('browser-*.json'))[-1].read_text())
assert browser['status'] == 'PASS' and browser['submission_id'] == 1
assert browser['displayed_verdict'] == 'AC' and browser['displayed_case_count'] == 103
assert browser['actual_native_form_post_count'] == 1 and browser['page_error_count'] == 0
result = json.loads((OUT / 'result.json').read_text())
compiler = json.loads((OUT / 'compiler-message-encoding.json').read_text())
assert compiler['status'] == 'PASS' and compiler['native_SQL_message_sha256'] == result['compiler_message_sha256']
assert compiler['warning_count'] == result['compiler_warning_count'] == 3
assert result['acceptance'] == 'PASS' and result['status'] == 'D' and result['verdict'] == 'AC'
assert result['language'] == 'CPP23' and result['judge'] == 'cpjudge-local-worker'
assert result['case_points'] == result['case_total'] == result['points'] == 103
assert not result['contest_attached'] and not result['pretests_only'] and result['language_limits'] == 0
cases = json.loads((OUT / 'cases.json').read_text())
assert [c['case'] for c in cases] == list(range(1, 104))
assert all(c['status'] == 'AC' and c['points'] == c['total'] == 1 for c in cases)
trace = json.loads((OUT / 'native-trace.json').read_text())
sent = [row for row in trace if row['direction'] == 'sent' and row['name'] == 'submission-request']
assert len(sent) == 1 and sent[0]['submission-id'] == 1
assert sent[0]['time-limit'] == 2.0 and sent[0]['memory-limit'] == 262144
assert sent[0]['language'] == 'CPP23' and sent[0]['short-circuit'] is False
assert sent[0]['source_sha256'] == browser['browser_form_post']['source_sha256'] == result['source_sha256']
callback = sorted([case for row in trace if row['name'] == 'test-case-status' for case in row['cases']], key=lambda c: c['position'])
assert len(callback) == 103 and any(row['name'] == 'grading-end' for row in trace)
for a, b in zip(callback, cases):
    assert a['position'] == b['case'] and a['status'] == 0
    assert (a['time'], a['memory'], a['points'], a['total-points']) == (b['time'], b['memory'], b['points'], b['total'])
with zipfile.ZipFile(ROOT / 'local-packages/gaming-grid.zip') as package:
    xml = ET.fromstring(package.read('problem.xml'))
    main = [s for s in xml.findall('assets/solutions/solution') if s.get('tag') == 'main']
    assert len(main) == 1 and main[0].find('source').get('type').endswith('g++23')
    reference = package.read(main[0].find('source').get('path')).decode().replace('\r\n', '\n')
    assert reference == reference.strip()
    assert hashlib.sha256(reference.encode()).hexdigest() == browser['reference_source_sha256'] == result['source_canonical_sha256']
worker = json.loads((OUT / 'worker-log-summary.json').read_text())
raw = (ROOT / worker['raw_private_log']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == worker['raw_log_sha256']
assert len(worker['matched_submission_lines']) == 3 and worker['explicit_native_worker_AC_cases'] == 103
native_case_matches = re.findall(r'Test case\s+(\d+)\s+AC\s+\[', (OUT / 'native-worker-cases.log').read_text())
assert list(map(int, native_case_matches)) == list(range(1, 104))
preserve = json.loads(sorted(OUT.glob('preserve-submit-*.json'))[-1].read_text())
assert preserve['status'] == 'PASS' and preserve['full_datetime_precision']
assert preserve['expected_new_native_rows'] == {'judge.submission': 1, 'judge.submissionsource': 1, 'judge.submissiontestcase': 103}
privacy = json.loads(sorted(OUT.glob('privacy-*.json'))[-1].read_text())
assert privacy['status'] == 'PASS'
assert sum(sum(counts.values()) for groups in privacy['responses'].values() for counts in groups.values()) == 696
registry = json.loads((ROOT / 'build/b05-problem-1/private/registry.json').read_text())
assert canonical_digest(registry['manifest']) == registry['manifest_digest']
assert file_manifest(ROOT / 'build/b03-worker-1/problems/pv000000000000000001') == registry['manifest']['files']
for name, sha in json.loads((ROOT / 'build/b05-problem-1/private/preserved-source.json').read_text()).items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
secrets = [json.loads((ROOT / 'build/b03-worker-1/private/worker.json').read_text())['key']]
for row in json.loads((ROOT / 'build/b01-site-1/private/accounts.json').read_text()).values():
    secrets.extend(row.values())
for path in (ROOT / 'build/b01-site-1/private').glob('*.env'):
    secrets.extend(line.split('=', 1)[1] for line in path.read_text().splitlines() if '=' in line)
for phase in ('b06-statement-1', 'b07-submission-1'):
    for path in (ROOT / 'build' / phase / 'browser').glob('*/sessions.json'):
        secrets.extend(json.loads(path.read_text()))
for path in (ROOT / 'build/b05-problem-1/logs').glob('*/temporary-privacy-session.log'):
    text = path.read_text()
    if 'OPERATOR_RESULT=' in text:
        secrets.append(json.loads(text.split('OPERATOR_RESULT=', 1)[1])['key'])
before = json.loads((ROOT / 'build/b06-statement-1/before.json').read_text())
for path in ROOT.rglob('*'):
    if not path.is_file() or any(part in ('build', '.git', '.venv', '.deps', 'local-packages', 'node_modules', '__pycache__') for part in path.parts):
        continue
    name = str(path.relative_to(ROOT))
    if name in before and name not in changes:
        continue
    data = path.read_bytes()
    assert not any(str(secret).encode() in data for secret in secrets if len(str(secret)) >= 6), name
assert subprocess.run(['git', 'diff', '--check'], cwd=ROOT).returncode == 0
for path in ('local-packages/gaming-grid.zip', 'build/b06-statement-1', 'build/b07-submission-1'):
    assert subprocess.run(['git', 'check-ignore', '-q', path], cwd=ROOT).returncode == 0
audit = {'status': 'PASS', 'command': '.venv/bin/python -B reports/b07-submission-1/verify_evidence.py',
         'exit_status': 0, 'baseline_files': counts, 'changed_existing_files': sorted(changes),
         'historical_reports_and_pins_preserved': True, 'immutable_worker_files_config_key_exact': True,
         'public_credential_values_found': False, 'precise_native_row_preservation': True,
         'B06': 'PASS', 'B07': 'PASS', 'submission_id': 1, 'verdict': 'AC', 'cases': 103,
         'actual_request_seconds': 2.0, 'actual_request_KiB': 262144,
         'native_browser_worker_callback_SQL_agreement': True, 'compiler_warnings_retained': 3,
         'git_diff_check_exit': 0, 'B08': 'NOT STARTED', 'contest_standings': 'NOT TESTED'}
(OUT / 'evidence-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print('PASS: B06/B07 reviewed evidence, real submission1/103AC, limits, privacy and preservation.')
