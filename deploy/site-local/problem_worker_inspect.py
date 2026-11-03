"""Hash upstream source and record relevant native semantics; no execution."""
import hashlib
import json
from pathlib import Path

root = Path('/judge/dmoj')
names = ['problem.py', 'packet.py', 'judgeenv.py', 'judge.py', 'checkers/bridged.py']
texts = {name: (root / name).read_text() for name in names}
assert "packet['time-limit']" in texts['packet.py'] and "packet['memory-limit']" in texts['packet.py']
assert 'time_limit' in texts['problem.py'] and 'memory_limit' in texts['problem.py']
semantics = {name: [line.strip() for line in text.splitlines() if any(token in line for token in
             ('time_limit', 'memory_limit', "['time-limit']", "['memory-limit']", 'sys_byteorder', 'short_circuit'))]
             for name, text in texts.items() if name in ('packet.py', 'problem.py')}
print(json.dumps({'pin': Path('/judge-source-commit').read_text().strip(),
      'source_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in texts.items()},
      'limit_semantics': semantics}, indent=2))
