"""Precise private row snapshots; allow only task-owned presentation/activity."""
import datetime
import json
import os
from pathlib import Path
from django.apps import apps
from django.contrib.auth.models import User
from judge.models import Problem

def encode(value):
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    return str(value)

path = Path('/tmp/b06-before.json')
state = {}
for model in apps.get_models(include_auto_created=True):
    if model._meta.label_lower == 'judge.runtimeversion':
        continue
    rows = list(model.objects.order_by('pk').values())
    if model._meta.label_lower == 'judge.judge':
        for row in rows:
            for key in ('online', 'ping', 'load', 'start_time', 'last_ip'):
                row.pop(key)
    state[model._meta.label_lower] = rows
state = json.loads(json.dumps(state, default=encode))
if MODE == 'snapshot':
    assert not path.exists()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.write(fd, json.dumps(state).encode()); os.close(fd)
    result = {'status': 'CAPTURED', 'models': len(state), 'datetime_precision': 'full isoformat microseconds'}
else:
    before = json.loads(path.read_text())
    user = User.objects.filter(is_staff=False, is_superuser=False, is_active=True).order_by('pk').first()
    p = Problem.objects.get(code='pv000000000000000001')
    changes = {}
    for name, rows in before.items():
        if name == 'judge.problem_testers':
            assert all(row in state[name] for row in rows)
            added = [row for row in state[name] if row not in rows]
            assert len(added) <= 1 and all(row['problem_id'] == p.pk and row['profile_id'] == user.profile.pk for row in added)
            continue
        assert len(rows) == len(state[name]), name
        for a, b in zip(rows, state[name]):
            fields = {key for key in a if a[key] != b[key]}
            if not fields:
                continue
            if name == 'judge.problem':
                assert a['id'] == p.pk and fields <= {'description'}, fields
            elif name == 'auth.user':
                assert a['id'] == user.pk and fields <= {'last_login'}, fields
            elif name == 'judge.profile':
                assert a['user_id'] == user.pk and fields <= {'last_access', 'ip'}, fields
            else:
                raise AssertionError(name)
            changes[name] = sorted(fields)
    result = {'status': 'PASS', 'models': len(before), 'precise_baseline': True,
              'expected_presentation_and_native_activity_fields': changes,
              'passwords_existing_domain_and_worker_auth_unchanged': True,
              'private_access': not p.is_public, 'judging': 'NOT TESTED'}
print('JOURNEY_RESULT=' + json.dumps(result, indent=2))
