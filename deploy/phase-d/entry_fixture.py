"""New task-owned native fixture; reuse the existing immutable version and probe."""
import json
from pathlib import Path
from datetime import timedelta
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from judge.models import Contest,ContestProblem,Submission
from cpjudge.models import ProblemVersion,ProblemProbe,ContestWorkflow,ContestProblemLabel,Identity
from cpjudge.contest_manage import FIXED
from cpjudge.policy import grant_scope,CAPABILITIES
from cpjudge.admission import approve
from cpjudge.publication import verify_native
from cpjudge.contest_readiness import check
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
U=get_user_model();v=ProblemVersion.objects.get(pk=2);owner=v.job.owner;operator=U.objects.get(pk=1)
assert verify_native(v)
probe=ProblemProbe.objects.filter(version=v,owner=owner,execution__result='AC',execution__status='D').latest('pk')
assert not Contest.objects.filter(key='d07local2').exists(),'Resume existing fixture rather than replace it.'
with transaction.atomic():
 now=timezone.now()
 c=Contest.objects.create(key='d07local2',name='D07 registration and removal acceptance',description='Local supervised competition fixture.',start_time=now+timedelta(seconds=45),end_time=now+timedelta(minutes=45),is_visible=True,**FIXED)
 ContestWorkflow.objects.create(contest=c,owner=owner,published_at=now)
 cp=ContestProblem.objects.create(contest=c,problem=v.problem,order=0,points=1,partial=False)
 ContestProblemLabel.objects.create(contest_problem=cp,label='A')
 for cap in CAPABILITIES-{'clarifications.edit','roster.export'}:grant_scope(operator,owner,c,cap)
 approval=approve(owner,v,c,probe)
 check(v.code,approval.runtime.key)
other=Identity.objects.filter(is_author=True,user__is_superuser=False).exclude(user=owner).select_related('user').first().user
accounts=[{'role':role,'username':u.username,'email':u.email} for role,u in [('author',owner),('participant',U.objects.get(pk=2)),('late',U.objects.get(pk=7)),('unrelated',other)]]
data={'contest':c.key,'contest_id':c.pk,'start':c.start_time.isoformat(),'end':c.end_time.isoformat(),'version':v.pk,'code':v.code,'runtime_id':approval.runtime_id,'accounts':accounts,'source':probe.solution.source,'expected_cases':len(v.manifest['test_cases'])}
p=Path('/tmp/d07-browser.json');p.write_text(json.dumps(data));p.chmod(0o600)
print('New published task-owned fixture prepared with original version/probe, common clock, and four existing accounts; no credentials changed.')
