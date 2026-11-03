"""Verify native SQL/collected compiler message newline equivalence, no text output."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
result = json.loads((OUT / 'result.json').read_text())
commands = json.loads((OUT / 'commands.json').read_text())
row = [r for r in commands if r.get('name') == 'retained-native-compiler-messages'][-1]
data = (ROOT / row['log']).read_bytes()
assert data.count(b'warning:') == result['compiler_warning_count'] == 3
assert len(data.splitlines()) == result['compiler_message_lines'] == 10
native = result['compiler_message_sha256']
raw_sha = hashlib.sha256(data).hexdigest()
lf = data.replace(b'\r\n', b'\n')
assert native in (raw_sha, hashlib.sha256(lf.replace(b'\n', b'\r\n')).hexdigest())
report = {'status': 'PASS', 'native_SQL_message_sha256': native,
          'collected_private_log_sha256': raw_sha,
          'LF_canonical_sha256': hashlib.sha256(lf).hexdigest(),
          'difference': 'newline encoding only; subprocess text mode collects LF',
          'warning_count': 3, 'lines': 10,
          'command': '.venv/bin/python -B reports/b07-submission-1/verify_compiler_messages.py', 'exit_status': 0}
(OUT / 'compiler-message-encoding.json').write_text(json.dumps(report, indent=2) + '\n')
print('PASS: retained compiler messages match native SQL hash after newline-only normalization.')
