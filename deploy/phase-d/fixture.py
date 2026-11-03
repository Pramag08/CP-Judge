import json
from pathlib import Path
from cpjudge.models import ProblemVersion,ProblemProbe,Grant,Identity
from cpjudge.publication import verify_native
from cpjudge.contest_readiness import check
v=ProblemVersion.objects.get(pk=2);assert verify_native(v)
a=v.job.owner
probe=ProblemProbe.objects.filter(version=v,execution__result='AC',execution__status='D',owner=a).latest('pk')
others=Identity.objects.filter(is_author=True).exclude(user=a).select_related('user')
p=Identity.objects.filter(user_id=2).select_related('user').get()
b=others.exclude(user__is_superuser=True).first()
assert b and a.identity.is_author
accounts=[{'role':role,'username':u.username,'email':u.email} for role,u in [('author',a),('participant',p.user),('unrelated',b.user)]]
data={'version':v.pk,'code':v.code,'probe':probe.pk,'accounts':accounts,'time_limit':v.problem.time_limit,'memory_limit':v.problem.memory_limit}
f=Path('/tmp/d01-browser.json');f.write_text(json.dumps(data));f.chmod(0o600)
print('Existing immutable version/probe and three existing scoped accounts selected privately.')
