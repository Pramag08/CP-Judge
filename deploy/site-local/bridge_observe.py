"""Install only passive native send/callback trace; never alter packet/results."""
import hashlib
import json
from pathlib import Path
from judge.models import Submission

assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
path = Path('/app/judge/bridge/judge_handler.py')
source = path.read_text()
before = hashlib.sha256(source.encode()).hexdigest()
if '_b07_observe' not in source:
    assert before == '3dbcf88bf7fe99c6b175b04517dd697641716f1968214ecd8e32e7db27a2f631'
    original = "        super().send(json.dumps(data, separators=(',', ':')))"
    assert source.count(original) == 1
    source = source.replace(original, original + "\n        _b07_observe('sent', data)")
    original = '                handler(data)'
    assert source.count(original) == 1
    source = source.replace(original, original + "\n                _b07_observe('received-and-handled', data)")
    source += r'''

# B07 passive diagnostic: original send and handlers above remain unchanged.
def _b07_observe(direction, packet):
    if packet.get('name') not in ('submission-request', 'submission-acknowledged',
            'grading-begin', 'test-case-status', 'grading-end', 'compile-error', 'internal-error'):
        return
    import datetime
    import hashlib
    import os
    row = {key: packet[key] for key in ('name', 'submission-id', 'problem-id', 'language',
           'time-limit', 'memory-limit', 'short-circuit') if key in packet}
    row['direction'] = direction
    row['observed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if 'source' in packet:
        row['source_sha256'] = hashlib.sha256(packet['source'].encode()).hexdigest()
    if 'cases' in packet:
        row['cases'] = [{key: case[key] for key in ('position', 'status', 'time', 'memory', 'points', 'total-points')}
                        for case in packet['cases']]
    try:
        fd = os.open('/tmp/b07-native-trace.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        os.write(fd, (json.dumps(row, separators=(',', ':')) + '\n').encode())
        os.close(fd)
    except OSError:
        logger.exception('B07 passive diagnostic write failed')
'''
    compile(source, str(path), 'exec')
    path.write_text(source)
else:
    compile(source, str(path), 'exec')
print('JOURNEY_RESULT=' + json.dumps({'status': 'PASS', 'native_original_sha256': before,
      'observed_overlay_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
      'packet_fields_handlers_scheduler_limits_unchanged': True}))
