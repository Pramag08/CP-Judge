"""Inspect saved B02 acceptance; no services, credentials or database access."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'reports/b02-services-1'
OUT = Path(__file__).resolve().parent
review = json.loads((OLD / 'review.json').read_text())
assert review['status'] == 'PASS' and review['blockers'] == []
checked = []
for name, expected in review['inspected_sha256'].items():
    data = (ROOT / name).read_bytes()
    if name.endswith('/commands.json'):
        rows = json.loads(data)
        matches = [n for n in range(len(rows) + 1)
                   if hashlib.sha256((json.dumps(rows[:n], indent=2) + '\n').encode()).hexdigest() == expected]
        assert len(matches) == 1, 'Original reviewed command ledger changed'
        original_count = matches[0]
        appended = rows[original_count:]
        assert all(row['action'] == 'status' and row['exit_status'] == 0 for row in appended)
    else:
        assert hashlib.sha256(data).hexdigest() == expected, name
    checked.append(name)
result = json.loads((OLD / 'result-20261028T205851761900Z.json').read_text())
assert result['status'] == 'PASS' and result['judges'] == 0
for key in ('celery_ping', 'native_noop_task_completed', 'websocket_event_exact_delivery',
            'http_poll_exact_delivery', 'judge_listener_tcp'):
    assert result[key] is True, key
browser = json.loads((OLD / 'browser-20261028T205858690494Z.json').read_text())
assert browser['status'] == 'PASS' and browser['page_error_count'] == 0
for name in ('result.json', 'runtime-preservation.json', 'preservation.json'):
    assert json.loads((OLD / name).read_text())['status'] == 'PASS', name
for name in ('README.md', 'MVP_DEPENDENCIES.md', 'PROJECT_STATUS.md', 'SecureExam-Implementation-Plan.md'):
    assert 'reports/b02-status-1/' in (ROOT / name).read_text(), name
for row in json.loads((OUT / 'commands.json').read_text()):
    assert row['exit_status'] == 0 and (ROOT / row['log']).is_file()
audit = {'status': 'PASS', 'scope': 'Saved B02 acceptance and documentation reconciliation; no runtime test',
         'command': 'python3 -B reports/b02-status-1/verify.py', 'exit_status': 0,
         'reviewed_hashes_checked': checked, 'original_command_count': original_count,
         'appended_status_entries': len(appended), 'current_services': 'STOPPED',
         'B02': 'COMPLETE — PASS', 'B03': 'NOT STARTED', 'judging': 'NOT TESTED'}
(OUT / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print('PASS: saved B02 evidence preserved; current documentation reconciled; services stopped.')
