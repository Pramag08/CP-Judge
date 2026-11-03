"""Only install the sanitized presentation and native private tester grant."""
import hashlib
import json
from pathlib import Path
from django.contrib.auth.models import User
from django.db import transaction
from judge.models import Problem, LanguageLimit

root = Path('/app/private-imports/pv000000000000000001')
receipt = json.loads((root / 'receipt.json').read_text())
description = (root / 'description.html').read_text()
assert hashlib.sha256(description.encode()).hexdigest() == receipt['description_sha256']
with transaction.atomic():
    p = Problem.objects.select_for_update().get(code=receipt['code'])
    assert not p.is_public and p.is_manually_managed and p.time_limit == 2 and p.memory_limit == 262144
    assert list(p.allowed_languages.values_list('key', flat=True)) == ['CPP23'] and not LanguageLimit.objects.filter(problem=p).exists()
    assert p.description in ('', description), 'Unknown existing presentation'
    user = User.objects.filter(is_staff=False, is_superuser=False, is_active=True).order_by('pk').first()
    assert user and not user.has_perm('judge.see_private_problem') and not p.is_editable_by(user)
    p.description = description; p.save(update_fields=['description'])
    p.testers.add(user.profile)
    assert p.is_accessible_by(user) and not p.is_editable_by(user)
print('JOURNEY_RESULT=' + json.dumps({'status': 'PASS', 'problem': p.code, 'private': True,
      'native_tester_grant': True, 'participant_staff_superuser': False, 'participant_edit_access': False,
      'description_sha256': receipt['description_sha256'], 'limits_unchanged': True}))
