"""Read-only server receipt/results; separate manual expectations from native scores."""
import hashlib,json,math
from judge.models import Contest,Submission
from judge.views.contests import get_contest_ranking_list
from types import SimpleNamespace
c=Contest.objects.get(key='b10b11local1')
submissions=[]
for s in Submission.objects.filter(contest_object=c).select_related('user__user','source','contest').order_by('date','id'):
 submissions.append({'id':s.pk,'username':s.user.user.username,'receipt':s.date.isoformat(),'status':s.status,'verdict':s.result,
    'case_points':s.case_points,'case_total':s.case_total,'case_count':s.test_cases.count(),'contest_points':s.contest.points,
    'source_sha256':hashlib.sha256(s.source.source.encode()).hexdigest(),'judged_on':s.judged_on_id,
    'case_statuses':list(s.test_cases.order_by('case').values_list('status',flat=True)),
    'participation_id':s.contest.participation_id})
entries=list(c.users.filter(virtual=0).select_related('user__user').order_by('id'))
expected=[]
for entry in entries:
 own=[s for s in submissions if s['username']==entry.user.user.username]
 full=next((s for s in own if s['status']=='D' and s['verdict']=='AC' and s['case_total']>0 and s['case_points']==s['case_total']),None)
 # One problem: hand calculation is elapsed whole seconds + 1200 for each prior qualifying failure.
 prior=own[:own.index(full)] if full else []
 failures=sum(s['status']=='D' and s['verdict'] in ('WA','TLE','MLE','RTE') for s in prior)
 from datetime import datetime
 elapsed=math.floor((datetime.fromisoformat(full['receipt'])-c.start_time).total_seconds()) if full else 0
 expected.append({'username':entry.user.user.username,'entry_id':entry.pk,'solved':int(full is not None),'elapsed_seconds':elapsed,
    'qualifying_failures':failures,'penalty_seconds':elapsed+1200*failures if full else 0,'first_ac_id':full['id'] if full else None,
    'join':entry.real_start.isoformat(),'common_start':entry.start.isoformat(),'common_end':entry.end_time.isoformat()})
expected.sort(key=lambda r:(-r['solved'],r['penalty_seconds'],r['entry_id']))
for i,row in enumerate(expected):
 row['rank']=expected[i-1]['rank'] if i and (row['solved'],row['penalty_seconds'])==(expected[i-1]['solved'],expected[i-1]['penalty_seconds']) else i+1
request=SimpleNamespace(user=entries[0].user.user,profile=entries[0].user)
ranking,_=get_contest_ranking_list(request,c,show_current_virtual=False)
actual=[{'username':row.username,'rank':rank,'solved':row.points,'penalty_seconds':row.cumtime,'tiebreaker':row.tiebreaker} for rank,row in ranking]
print('JOURNEY_RESULT='+json.dumps({'start':c.start_time.isoformat(),'end':c.end_time.isoformat(),'format':c.format_name,
 'submissions':submissions,'manual_expected':expected,'actual':actual,
 'standings_match':[{k:r[k] for k in ('username','rank','solved','penalty_seconds')} for r in expected]==[{k:r[k] for k in ('username','rank','solved','penalty_seconds')} for r in actual]}))
