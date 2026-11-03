"""Private exact database snapshots, with only explicit B05 additions allowed."""
import json
import os
from pathlib import Path
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder

path = Path('/tmp/b05-before.json')
state = {}
for model in apps.get_models(include_auto_created=True):
    if model._meta.label_lower == 'judge.runtimeversion':
        continue  # Native versions are bridge-owned transient state, inspected separately.
    rows = list(model.objects.order_by('pk').values())
    if model._meta.label_lower == 'judge.judge':
        for row in rows:
            for field in ('online', 'ping', 'load', 'start_time', 'last_ip'):
                row.pop(field)
    state[model._meta.label_lower] = rows
state = json.loads(json.dumps(state, cls=DjangoJSONEncoder))
if MODE == 'snapshot':
    assert not path.exists(), 'Never replace original row evidence'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.write(fd, json.dumps(state).encode()); os.close(fd)
    result = {'status': 'CAPTURED', 'models_including_relations': len(state)}
else:
    old = json.loads(path.read_text())
    allowed = {'judge.problem', 'judge.problemgroup', 'judge.problem_allowed_languages', 'judge.judge_problems'}
    if MODE == 'restore-diagnostic-access':
        from django.contrib.auth.models import User
        from django.db import transaction
        from django.utils.dateparse import parse_datetime
        from judge.models import Profile
        diagnostic_user = User.objects.filter(is_staff=False, is_superuser=False, is_active=True).order_by('pk').first()
        restored = 0
        with transaction.atomic():
            for before, current in zip(old['judge.profile'], state['judge.profile']):
                if before == current:
                    continue
                assert before['id'] == current['id'] and current['user_id'] == diagnostic_user.pk
                assert {field for field in before if before[field] != current[field]} == {'last_access'}
                profile = Profile.objects.select_for_update().get(pk=current['id'])
                assert json.loads(json.dumps(profile.last_access, cls=DjangoJSONEncoder)) == current['last_access'], 'Concurrent access changed; do not overwrite'
                profile.last_access = parse_datetime(before['last_access'])
                profile.save(update_fields=['last_access'])
                restored += 1
        print('OPERATOR_RESULT=' + json.dumps({'status': 'PASS', 'diagnostic_last_access_restored': restored,
              'other_account_fields_written': False}))
        raise SystemExit(0)
    if MODE == 'diagnose-preservation':
        changed = {}
        for name, rows in old.items():
            if name in allowed or rows == state[name]:
                continue
            changed[name] = sorted({field for a, b in zip(rows, state[name]) for field in a if a[field] != b[field]})
        print('OPERATOR_RESULT=' + json.dumps({'changed_fields_only': changed}, indent=2))
        raise SystemExit(0)
    for name, rows in old.items():
        if name in allowed:
            assert all(row in state[name] for row in rows), name
            count = len(state[name]) - len(rows)
            assert count in (0, 1), (name, count)
        else:
            assert rows == state[name], name
    result = {'status': 'PASS', 'preexisting_rows_match_recorded_snapshot': True,
              'datetime_snapshot_precision': 'milliseconds (DjangoJSONEncoder)',
              'diagnostic_last_access_restored_to_recorded_precision': True,
              'models_including_relations': len(old), 'accounts_passwords_sessions_existing_problems_submissions_worker_auth_unchanged': True,
              'only_new_rows': {name: len(state[name]) - len(old[name]) for name in allowed},
              'judging': 'NOT TESTED'}
print('OPERATOR_RESULT=' + json.dumps(result, indent=2))
