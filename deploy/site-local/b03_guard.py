"""Permit only the owned idle B03 registration; upstream resets jobs on start."""
import json
from pathlib import Path
from judge.models import Judge, Submission

assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists(), 'Refusing bridge lifecycle with in-progress jobs'
owned = json.loads(Path('/tmp/b03-registration.json').read_text())
assert not Judge.objects.exclude(name=owned['id']).exists(), 'Unknown judge registration; review before bridge restart'
for judge in Judge.objects.all():
    assert judge.auth_key == owned['key'] and not judge.is_blocked
print('Bridge guard: only owned B03 registration; no in-progress submissions.')
