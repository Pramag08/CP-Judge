"""Read-only actual site source/model inspection for B04."""
import hashlib
import json
from pathlib import Path
from judge.models import Problem, ProblemGroup, Language, Judge

for rel, expected in EXPECTED.items():
    assert hashlib.sha256((Path('/app') / rel).read_bytes()).hexdigest() == expected, rel
assert Problem._meta.get_field('code').max_length == 20
assert Problem._meta.get_field('code').unique
assert Language.objects.filter(key='CPP23', info='').exists()
cpp_online = Judge.objects.filter(name='cpjudge-local-worker', online=True, runtimes__key='CPP23').exists()
print('OPERATOR_RESULT=' + json.dumps({'site_pin': '604d60cfd764bc708b04ffd75b715a5398b91f8b',
      'groups': list(ProblemGroup.objects.order_by('pk').values('id', 'name', 'full_name')),
      'CPP23_online': cpp_online, 'source_hashes_match_selected_checkout': True}, indent=2))
