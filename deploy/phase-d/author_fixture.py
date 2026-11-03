"""Read existing fixture only; never extend schedules or replace participants."""
import json,hashlib
from pathlib import Path
from django.contrib.auth import get_user_model
from judge.models import Contest,Submission,Judge
from cpjudge.models import ProblemVersion,ProblemProbe,ContestVersionAdmission,Identity
from cpjudge.publication import verify_native
from cpjudge.contest_readiness import check
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
c=Contest.objects.get(key='d07local2');a=ContestVersionAdmission.objects.get(contest_problem__contest=c);v=a.version
assert verify_native(v);check(v.code,a.runtime.key)
U=get_user_model();owner=c.workflow.owner
other=Identity.objects.filter(is_author=True,user__is_superuser=False).exclude(user=owner).first().user
accounts=[{'role':role,'username':u.username,'email':u.email} for role,u in [('author',owner),('participant',U.objects.get(pk=7)),('removed',U.objects.get(pk=2)),('unrelated',other)]]
wrong=ProblemProbe.objects.filter(version=v,execution__result='WA',execution__status='D').latest('pk')
data={'contest':c.key,'contest_id':c.pk,'version':v.pk,'code':v.code,'runtime_id':a.runtime_id,'accounts':accounts,'source':a.probe.solution.source,'wrong':wrong.solution.source,'expected_cases':len(v.manifest['test_cases'])}
p=Path('/tmp/d13-browser.json');p.write_text(json.dumps(data));p.chmod(0o600)
print('Existing selected version, AC/WA sources and accounts reused privately; fresh worker readiness verified. No schedule/account/data change.')
