import json
from pathlib import Path
from django.apps import apps
from judge.models import Submission
from cpjudge.email_identity import inventory,email_only
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
assert not email_only()
_,issues=inventory();assert {row['user_id'] for row in issues}=={1,2,7,8}
p=Path('/tmp/c18-cutover-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('Private all-model baseline retained; four blank-email fixtures and transitional mode confirmed.')
