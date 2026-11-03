"""Focused constructed checks for scorer differences; not new judged submissions."""
import datetime,json
from types import SimpleNamespace
from django.core.exceptions import ValidationError
from judge.contest_format.cpjudge_icpc import full_ac,score_attempts,CPJudgeICPCFormat
from judge.utils.ranker import ranker
S=datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc)
def row(i,seconds,result='AC',problem=1,status='D',points=None,total=1):
 return {'id':i,'date':S+datetime.timedelta(seconds=seconds),'result':result,'status':status,
  'case_points':int(result=='AC') if points is None else points,'case_total':total,'problem_id':problem}
checks=[]
def check(name,got,wanted):assert got==wanted,(name,got,wanted);checks.append(name)
check('rounded partial is not full AC',full_ac('D','AC',9996,10000),False)
check('non-AC full points not solved',full_ac('D','RTE',1,1),False)
check('pending old AC not solved',full_ac('G','AC',1,1),False)
check('empty case set not solved',full_ac('D','AC',0,0),False)
check('floor separately per solved problem',score_attempts(S,[row(1,60.6),row(2,120.6,problem=2)])[:2],(2,180))
fail=[row(i+1,i+1,result=r) for i,r in enumerate(['WA','TLE','MLE','RTE','CE','IE','OLE','IR','SC','AB'])]
check('exact qualifying failures and CE exclusions',score_attempts(S,fail+[row(20,2100)])[:2],(1,6900))
check('unsolved zero penalty',score_attempts(S,fail)[:2],(0,0))
check('same receipt uses ID; later WA ignored',score_attempts(S,[row(2,60,'WA'),row(1,60)])[:2],(1,60))
check('later failures ignored',score_attempts(S,[row(1,60),row(2,61,'WA')])[:2],(1,60))
seq=[row(1,600,'WA'),row(2,2100)]
check('authoritative original result',score_attempts(S,seq)[:2],(1,3300))
check('authoritative replacement WA to CE',score_attempts(S,[row(1,600,'CE'),seq[1]])[:2],(1,2100))
check('authoritative replacement AC to WA',score_attempts(S,[seq[0],row(2,2100,'WA')])[:2],(0,0))
check('replacement pending withholds old credit',score_attempts(S,[seq[0],row(2,2100,status='G')])[:2],(0,0))
ordered=[SimpleNamespace(points=2,cumtime=3600,tiebreaker=0),SimpleNamespace(points=2,cumtime=3600,tiebreaker=0),SimpleNamespace(points=1,cumtime=100,tiebreaker=0)]
check('native competition ranks', [r for r,_ in ranker(ordered,key=lambda p:(p.points,p.cumtime,p.tiebreaker))],[1,1,3])
for config in ({'penalty':19},{'penalty':True},{'penalty':20.0},{'penalty':20,'other':1}):
 try:CPJudgeICPCFormat.validate(config)
 except ValidationError:pass
 else:raise AssertionError(config)
checks.append('fixed config rejects alternate settings')
# Exercise the exact SQL ranking provider used by HTML/AJAX. Only derived fields
# on the two temporary entries are changed, inside a transaction rolled back.
from django.db import transaction
from judge.models import Contest,ContestParticipation
from judge.views.contests import get_contest_ranking_list
c=Contest.objects.get(key='b10b11local1')
a=c.users.get(user__user__username='b10tmpa');b=c.users.get(user__user__username='b10tmpb')
original=list(c.users.order_by('id').values('id','score','cumtime','tiebreaker'))
request=SimpleNamespace(user=a.user.user,profile=a.user)
def ranks():
 ranked,_=get_contest_ranking_list(request,c,show_current_virtual=False)
 return [(rank,p.username) for rank,p in ranked]
with transaction.atomic():
 ContestParticipation.objects.filter(pk=a.pk).update(score=1,cumtime=5000,tiebreaker=0)
 ContestParticipation.objects.filter(pk=b.pk).update(score=0,cumtime=0,tiebreaker=0)
 check('native SQL more solved outranks lower penalty',ranks(),[(1,'b10tmpa'),(2,'b10tmpb')])
 ContestParticipation.objects.filter(pk=b.pk).update(score=1,cumtime=6000)
 check('native SQL lower penalty outranks entry ID',ranks(),[(1,'b10tmpa'),(2,'b10tmpb')])
 ContestParticipation.objects.filter(pk=b.pk).update(cumtime=5000)
 check('native SQL tied pairs share rank and stable entry ID',ranks(),[(1,'b10tmpb'),(1,'b10tmpa')])
 transaction.set_rollback(True)
assert list(c.users.order_by('id').values('id','score','cumtime','tiebreaker'))==original
print('JOURNEY_RESULT='+json.dumps({'status':'PASS','checks':checks,'count':len(checks),
 'kind':'constructed scorer inputs/native ranker plus rollback-only SQL ordering fixtures on temporary entries; no new executions or operational rejudge test'}))
