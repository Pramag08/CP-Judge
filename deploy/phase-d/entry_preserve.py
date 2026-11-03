"""Narrow preservation and actual D11 standing/result verification."""
import json
from pathlib import Path
from django.apps import apps
from django.db import transaction
from judge.models import Contest,Profile,Submission,Judge
from cpjudge.models import ContestEntry,ContestReceipt,Audit,ProblemVersion
from cpjudge.entries import validate_receipt
before=json.loads(Path('/tmp/d07-before.json').read_text())
# Restore only the prior native navigation contexts of browser fixture accounts;
# registration records remain authoritative and independent of these pointers.
c=Contest.objects.get(key='d07local2')
fixture=json.loads(Path('/tmp/d07-browser.json').read_text())
handles={r['username'] for r in fixture['accounts']}
fixture_ids={r['id'] for r in before['auth.user'] if r['username'] in handles}
restored=0
with transaction.atomic():
 for old in before['judge.profile']:
  p=Profile.objects.get(pk=old['id'])
  if p.current_contest_id!=old['current_contest_id']:
   assert p.user_id in fixture_ids
   Profile.objects.filter(pk=p.pk).update(current_contest_id=old['current_contest_id']);restored+=1
allowed={'auth.user':{'last_login'},'judge.profile':{'last_access','ip'},'judge.judge':{'ping','load','last_ip','start_time'},'cpjudge.identity':{'generation'}}
count=0
for label,oldrows in before.items():
 if label=='sessions.session':continue
 model=apps.get_model(label);pk=model._meta.pk.attname
 current=json.loads(json.dumps(list(model.objects.all().values()),default=str))
 if label=='judge.runtimeversion':
  semantic=lambda rows:sorted(json.dumps({k:v for k,v in row.items() if k!='id'},sort_keys=True) for row in rows)
  assert semantic(oldrows)==semantic(current),'Runtime advertisement content changed';count+=len(oldrows);continue
 rows={r[pk]:r for r in current}
 for old in oldrows:
  assert old[pk] in rows,'Removed baseline row: '+label
  changed={k for k in old if old[k]!=rows[old[pk]][k]}
  permitted=allowed.get(label,set())
  if label=='judge.problem' and old[pk]==ProblemVersion.objects.get(pk=2).problem_id:permitted={'ac_rate','user_count'}
  assert changed<=permitted,(label,old[pk],sorted(changed))
  count+=1
s=Submission.objects.get(pk=23);r=ContestReceipt.objects.get(submission=s)
assert s.contest_object_id==c.pk and validate_receipt(s)
assert s.status=='D' and s.result=='AC' and s.case_points==s.case_total==3
assert list(s.test_cases.order_by('case').values_list('case','status','points','total'))==[(1,'AC',1,1),(2,'AC',1,1),(3,'AC',1,1)]
assert s.judged_on_id==Judge.objects.get(name='cpjudge-local-worker',online=True).pk
entry=r.entry;entry.participation.refresh_from_db()
assert entry.status=='dq' and entry.participation.is_disqualified and entry.participation.score==1
assert entry.participation.cumtime==int((s.date-c.start_time).total_seconds())
late=ContestEntry.objects.get(contest=c,user_id=7);assert late.status=='active'
assert late.registered_at>=c.start_time and late.participation.start==c.start_time and late.participation.end_time==c.end_time
from judge.views.contests import get_contest_ranking_list
request=__import__('types').SimpleNamespace(user=c.workflow.owner,profile=c.workflow.owner.profile)
rows,_=get_contest_ranking_list(request,c,show_current_virtual=False)
assert [(rank,row.participation.pk) for rank,row in rows]==[(1,late.participation_id)]
assert Audit.objects.filter(action='entry.remove',subject_id=2,scope=str(c.pk),details__reason='D11 browser removal acceptance').count()==1
assert Audit.objects.filter(action='entry.dq',subject_id=2,scope=str(c.pk),details__reason='D11 browser disqualification acceptance').count()==1
assert ContestReceipt.objects.filter(entry__contest=c).count()==1
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
result={'status':'PASS','baseline_model_sets':len(before),'baseline_non_session_rows':count,'original_password_hashes_accounts_imports_sources_cases_contests_audits_preserved':True,
 'native_runtime_advertisement_content_preserved':True,'original_navigation_contexts_restored':True,'native_problem_aggregate_updates_for_new_submission':True,'new_actual_submission':s.pk,'actual_verdict':'AC','actual_cases':3,
 'native_limits':[s.problem.time_limit,s.problem.memory_limit],'runtime':s.language.key,'one_durable_submission_receipt':True,'same_common_start_end_for_late_entrant':True,
 'dq_original_score_retained':entry.participation.score,'dq_excluded_from_rank':True,'remaining_entrant_rank':1,'removal_and_dq_reason_audits':True,'no_pending_work':True}
Path('/tmp/d07-preservation.json').write_text(json.dumps(result,indent=2))
print('PASS: all prior data retained; one actual AC3 receipt, reasoned removal/DQ and remaining entrant rank1 verified. Original navigation contexts restored.')
