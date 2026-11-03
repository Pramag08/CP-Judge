from cpjudge.models import ProbeSolution,ProblemProbe
print('solutions',ProbeSolution.objects.count(),'probes',list(ProblemProbe.objects.values_list('pk','execution__status','execution__result')))
