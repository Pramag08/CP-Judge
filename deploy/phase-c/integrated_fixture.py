import json
from pathlib import Path
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from judge.models import Contest,ContestProblem,Submission
from cpjudge.models import ProblemVersion,ProblemProbe
from cpjudge.policy import grant_scope
from cpjudge.admission import approve
from cpjudge.probes import binding
from cpjudge.publication import verify_native
from cpjudge.email_identity import email_only
assert not email_only()
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
U=get_user_model();owner=U.objects.get(username='C1LIVEA');operator=U.objects.get(pk=1)
v=ProblemVersion.objects.get(pk=2);assert verify_native(v)
probe=ProblemProbe.objects.get(pk=1,version=v);assert binding(probe)
assert probe.execution.result=='AC'
assert not Contest.objects.filter(key='cintlocal1').exists()
with transaction.atomic():
 now=timezone.now()
 c=Contest.objects.create(key='cintlocal1',name='Private same-version integration acceptance',description='Local acceptance fixture only. Existing imported version and accepted private probe; two existing individual test entrants.',start_time=now+timedelta(seconds=30),end_time=now+timedelta(minutes=45),is_visible=True,is_private=True,is_rated=False,time_limit=None,format_name='cpjudge_icpc_v1',format_config={'penalty':20},points_precision=0)
 cp=ContestProblem.objects.create(contest=c,problem=v.problem,order=0,points=1,partial=False)
 for cap in ('settings.edit','problems.publish','submissions.review','source.review','roster.read'):
  grant_scope(operator,owner,c,cap)
 for name in ('C1LIVEP','C1LIVEQ'):c.private_contestants.add(U.objects.get(username=name).profile)
 a=approve(owner,v,c,probe)
 assert verify_native(v)
meta={'contest':c.key,'contest_id':c.pk,'start':c.start_time.isoformat(),'end':c.end_time.isoformat(),
 'version_id':v.pk,'code':v.code,'digest':v.digest,'package_sha256':v.job.package_sha256,'job_id':v.job_id,'attempt':v.attempt,'probe_id':probe.pk,'admission_id':a.pk,'runtime':a.runtime.key,'runtime_id':a.runtime_id}
p=Path('/tmp/integrated-fixture.json');assert not p.exists();p.write_text(json.dumps(meta));p.chmod(0o600)
for name,source in [('accepted.cpp',probe.solution.source),('wrong.cpp',ProblemProbe.objects.get(pk=2,version=v).solution.source)]:
 p=Path('/tmp/integrated-'+name);assert not p.exists();p.write_text(source);p.chmod(0o600)
print('Private native contest/admission created for exact existing version and complete AC probe; only two existing test entrants allowlisted. No accounts/passwords/emails changed.')
