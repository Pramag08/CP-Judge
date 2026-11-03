"""Private exact row snapshots; public report contains only counts/hashes."""
import hashlib
import json
import os
from pathlib import Path
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection

path = Path('/tmp/b03-before.json')
state = {}
for model in apps.get_models():
    if model._meta.label_lower in ('judge.judge', 'judge.runtimeversion', 'judge.language'):
        continue
    # Every pre-existing row, including password hashes, sessions, problems and submissions.
    state[model._meta.label_lower] = list(model.objects.order_by('pk').values())
state['languages'] = list(apps.get_model('judge.Language').objects.order_by('pk').values())
state = json.loads(json.dumps(state, cls=DjangoJSONEncoder))
if MODE == 'snapshot':
    assert not path.exists(), 'Do not replace initial preservation evidence'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.write(fd, json.dumps(state).encode())
    os.close(fd)
    print(json.dumps({'status': 'CAPTURED', 'models': len(state), 'rows': sum(len(v) for v in state.values())}))
else:
    old = json.loads(path.read_text())
    for name, rows in old.items():
        if name == 'languages':
            assert all(row in state[name] for row in rows), name
            assert len(state[name]) - len(rows) in (0, 1)
        else:
            assert state[name] == rows, name
    with connection.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM django_migrations')
        migrations = cursor.fetchone()[0]
    assert migrations == 202
    for rel, expected in EXPECTED['runtime_overlay_sha256'].items():
        assert hashlib.sha256((Path('/app') / rel).read_bytes()).hexdigest() == expected, rel
    root = Path('/app/resources/vendor/mathjax-3.2.2')
    math = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    assert math == EXPECTED['math_files_sha256']
    assert hashlib.sha256(Path('/app/judge/migrations/0153_reconcile_model_metadata.py').read_bytes()).hexdigest() == EXPECTED['migration_0153_sha256']
    print(json.dumps({'status': 'PASS', 'all_preexisting_rows_exact': True,
                      'models': len(old), 'migrations': migrations,
                      'new_languages': len(state['languages']) - len(old['languages']),
                      'accounts_passwords_problems_submissions_unchanged': True,
                      'runtime_overlay_math_0153_exact': True}))
