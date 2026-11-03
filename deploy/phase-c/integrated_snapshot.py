import json
from pathlib import Path
from django.apps import apps
from django.contrib.auth import get_user_model
from judge.models import Submission,Judge
from cpjudge.email_identity import inventory,email_only
from cpjudge.models import ProblemVersion
from cpjudge.publication import verify_native
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
assert Judge.objects.get(name='cpjudge-local-worker').online
assert not email_only()
mapping,issues=inventory();assert [(r['user_id'],r['issue']) for r in issues]==[(1,'missing'),(2,'missing'),(7,'missing'),(8,'missing')]
v=ProblemVersion.objects.get(pk=2);assert verify_native(v)
p=Path('/tmp/integrated-before.json');assert not p.exists()
p.write_text(json.dumps({m._meta.label_lower:list(m.objects.all().values()) for m in apps.get_models() if not m._meta.proxy},default=str));p.chmod(0o600)
print('Current worker, unchanged four blank-email accounts, legacy mode and exact imported version confirmed; private baseline saved.')
