from cpjudge.models import ContestVersionAdmission,ProblemVersion
from cpjudge.publication import verify_native
from cpjudge.admission import verify_approval
from cpjudge.probes import binding
from cpjudge.contest_readiness import check
from judge.models import Contest
c=Contest.objects.get(key='d01local1');a=ContestVersionAdmission.objects.get(contest_problem__contest=c)
for name,func in [('version',lambda:verify_native(a.version)),('approval',lambda:verify_approval(a)),('probe',lambda:binding(a.probe)),('live',lambda:check(a.version.code,a.runtime.key))]:
 try:func();print(name,'PASS')
 except Exception as e:print(name,type(e).__name__,str(e))
print('languages',list(a.version.problem.allowed_languages.values_list('key',flat=True)),a.runtime.key)
