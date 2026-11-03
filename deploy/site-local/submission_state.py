"""B07 precise snapshots/read-only results; never write a verdict or Submission."""
import datetime
import hashlib
import json
import os
from pathlib import Path
from django.apps import apps
from django.contrib.auth.models import User
from judge.models import Problem, Submission

def encode(value):
    return value.isoformat() if isinstance(value, (datetime.datetime, datetime.date, datetime.time)) else str(value)

path = Path(globals().get('SNAPSHOT_PATH', '/tmp/b07-before.json'))
user = User.objects.filter(is_staff=False, is_superuser=False, is_active=True).order_by('pk').first()
p = Problem.objects.get(code='pv000000000000000001')
assert not p.is_public and p.is_accessible_by(user) and not p.is_editable_by(user)
if MODE == 'results':
    s = Submission.objects.select_related('language', 'judged_on', 'problem', 'user').get(pk=SUBMISSION_ID)
    assert s.user_id == user.profile.pk and s.problem_id == p.pk
    cases = list(s.test_cases.order_by('case').values('case', 'status', 'points', 'total', 'time', 'memory'))
    if s.error:
        fd = os.open('/tmp/b07-compiler-message.txt', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, s.error.encode()); os.close(fd)
    result = {'submission_id': s.pk, 'native_code': p.code, 'status': s.status, 'verdict': s.result,
              'language': s.language.key, 'judge': s.judged_on.name if s.judged_on else None,
              'source_sha256': hashlib.sha256(s.source.source.encode()).hexdigest(),
              'source_canonical_sha256': hashlib.sha256(s.source.source.replace('\r\n', '\n').strip().encode()).hexdigest(),
              'case_points': s.case_points, 'case_total': s.case_total, 'points': s.points,
              'time_seconds_sum': s.time, 'peak_memory_KiB': s.memory, 'cases': cases,
              'problem_time_seconds': p.time_limit, 'problem_memory_KiB': p.memory_limit,
              'language_limits': p.language_limits.count(), 'contest_attached': s.contest_object_id is not None,
              'pretests_only': s.is_pretested, 'error_present': bool(s.error)}
    result.update({'compiler_message_sha256': hashlib.sha256((s.error or '').encode()).hexdigest(),
                   'compiler_warning_count': (s.error or '').count('warning:'),
                   'compiler_message_lines': len((s.error or '').splitlines())})
else:
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
        if not globals().get('ALLOW_PRIOR', False):
            assert not Submission.objects.filter(problem=p).exists()
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, json.dumps(state).encode()); os.close(fd)
        result = {'status': 'CAPTURED', 'models': len(state), 'full_datetime_precision': True, 'prior_submissions': Submission.objects.count()}
    else:
        before = json.loads(path.read_text())
        additions = {}
        expected_new = globals().get('EXPECTED_NEW', {'judge.submission': 1, 'judge.submissionsource': 1, 'judge.submissiontestcase': 103})
        for name, rows in before.items():
            if name in expected_new:
                assert all(row in state[name] for row in rows)
                additions[name] = len(state[name]) - len(rows)
                assert additions[name] == expected_new[name], (name, additions[name])
                continue
            assert len(rows) == len(state[name]), name
            for a, b in zip(rows, state[name]):
                fields = {key for key in a if a[key] != b[key]}
                if not fields:
                    continue
                if name == 'auth.user':
                    assert a['id'] == user.pk and fields <= {'last_login'}
                elif name == 'judge.profile':
                    assert a['user_id'] == user.pk and fields <= {'last_access', 'ip'}
                elif name == 'judge.problem':
                    assert a['id'] == p.pk and fields <= {'user_count', 'ac_rate'}
                else:
                    raise AssertionError((name, fields))
        result = {'status': 'PASS', 'models': len(before), 'full_datetime_precision': True,
                  'expected_new_native_rows': additions, 'passwords_auth_limits_statement_existing_data_preserved': True,
                  'allowed_activity': 'native login/access and native problem AC statistics only'}
print('JOURNEY_RESULT=' + json.dumps(result, indent=2))
