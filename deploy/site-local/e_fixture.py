"""Additive temporary E acceptance fixture; never modifies existing rows."""
import json
from pathlib import Path
from datetime import timedelta
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from judge.models import Contest,ContestProblem,Submission
from cpjudge.models import ProblemVersion,ProblemProbe,ContestWorkflow,ContestProblemLabel,Identity
from cpjudge.email_identity import provision_email
from cpjudge.contest_manage import FIXED
from cpjudge.admission import approve
from cpjudge.publication import verify_native
from cpjudge.contest_readiness import check
from cpjudge.policy import grant_scope,CAPABILITIES
U=get_user_model();operator=U.objects.get(pk=1);v=ProblemVersion.objects.get(pk=2);owner=v.job.owner
assert verify_native(v)
probe=ProblemProbe.objects.filter(version=v,owner=owner,execution__result='AC',execution__status='D').latest('pk')
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
keys=('eaccept1','eaccept2','eupcoming1','eended1')
assert not Contest.objects.filter(key__in=keys).exists()
assert not Identity.objects.filter(canonical_email__endswith='@e-accept.example.test').exists()
with transaction.atomic():
    now=timezone.now();users=[]
    for role in ('primary','second','removed','empty'):
        u,pw=provision_email(operator,f'{role}@e-accept.example.test',first_name='E acceptance',last_name=role)
        users.append({'role':role,'email':u.email,'password':pw,'id':u.pk,'username':u.username})
    contests=[]
    for key,label,start,end,admit in (
        (keys[0],'E acceptance active primary',now+timedelta(seconds=90),now+timedelta(hours=3),True),
        (keys[1],'E acceptance active alternate',now+timedelta(seconds=90),now+timedelta(hours=3),True),
        (keys[2],'E acceptance upcoming',now+timedelta(hours=4),now+timedelta(hours=5),True),
        (keys[3],'E acceptance ended',now-timedelta(hours=3),now-timedelta(hours=2),False),
    ):
        c=Contest.objects.create(key=key,name=label,description='Temporary local development fixture for E browser acceptance.',start_time=start,end_time=end,is_visible=True,**FIXED)
        ContestWorkflow.objects.create(contest=c,owner=owner,published_at=now)
        cp=ContestProblem.objects.create(contest=c,problem=v.problem,order=0,points=1,partial=False)
        ContestProblemLabel.objects.create(contest_problem=cp,label='A')
        for cap in CAPABILITIES-{'clarifications.edit','roster.export'}:grant_scope(operator,owner,c,cap)
        if admit:
            a=approve(owner,v,c,probe);check(v.code,a.runtime.key)
        contests.append({'key':key,'start':start.isoformat(),'end':end.isoformat()})
    data={'label':'TEMPORARY E DEVELOPMENT FIXTURE','users':users,'contests':contests,'code':v.code,'runtime_id':probe.solution.runtime_id,'source':probe.solution.source,'expected_cases':len(v.manifest['test_cases'])}
    p=Path('/tmp/e-accept-fixture.json');assert not p.exists();p.write_text(json.dumps(data));p.chmod(0o600)
print('Created four additive labelled E contests and four reserved-email development accounts; fixture credentials written privately.')
