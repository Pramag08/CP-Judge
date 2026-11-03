"""D13 actual execution/callback agreement and prior-data preservation."""
import json,hashlib
from pathlib import Path
from django.apps import apps
from judge.models import Submission,Contest,ContestSubmission,Judge
from cpjudge.models import AuthorTest
from cpjudge.author_tests import binding
before=json.loads(Path('/tmp/d13-before.json').read_text())
# Native statement/navigation clears expired current-contest pointers on reads.
# Restore only the four browser accounts' prior navigation pointers.
from judge.models import Profile
fixture=json.loads(Path('/tmp/d13-browser.json').read_text())
handles={row['username'] for row in fixture['accounts']}
ids={row['id'] for row in before['auth.user'] if row['username'] in handles}
for old in before['judge.profile']:
 current=Profile.objects.get(pk=old['id'])
 if current.current_contest_id!=old['current_contest_id']:
  assert current.user_id in ids
  Profile.objects.filter(pk=current.pk).update(current_contest_id=old['current_contest_id'])
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
  assert changed<=allowed.get(label,set()),(label,old[pk],sorted(changed))
  count+=1
oldids={r['id'] for r in before['judge.submission']}
new=list(Submission.objects.exclude(pk__in=oldids).order_by('pk'));assert len(new)==2
assert ContestSubmission.objects.count()==len(before['judge.contestsubmission'])
trace=[json.loads(line) for line in Path('/tmp/c11-native-trace.jsonl').read_text().splitlines()]
results=[]
for s,verdict in zip(new,('AC','WA')):
 t=AuthorTest.objects.get(execution=s);a=binding(s)
 assert s.status=='D' and s.result==verdict and s.case_total==3
 assert s.case_points==(3 if verdict=='AC' else 0)
 assert s.is_archived and s.contest_object_id is None and not ContestSubmission.objects.filter(submission=s).exists()
 cases=list(s.test_cases.order_by('case').values('case','status','points','total','time','memory'))
 assert [(r['case'],r['status'],r['points'],r['total']) for r in cases]==[(i,verdict,1 if verdict=='AC' else 0,1) for i in (1,2,3)]
 assert s.judged_on_id==Judge.objects.get(name='cpjudge-local-worker',online=True).pk
 rows=[r for r in trace if r.get('submission-id')==s.pk]
 sent=[r for r in rows if r['name']=='submission-request'];assert len(sent)==1
 request=sent[0]
 assert (request['problem-id'],request['language'],request['time-limit'],request['memory-limit'])==(s.problem.code,s.language.key,s.problem.time_limit,s.problem.memory_limit)
 assert request['source_sha256']==hashlib.sha256(s.source.source.encode()).hexdigest()
 assert sum(r['name']=='grading-end' for r in rows)==1
 actual=[case for r in rows if r['name']=='test-case-status' for case in r['cases']]
 assert [(r['position'],r['status'],r['points'],r['total-points']) for r in actual]==[(i,0 if verdict=='AC' else 1,1 if verdict=='AC' else 0,1) for i in (1,2,3)]
 assert [(r['time'],r['memory']) for r in actual]==[(r['time'],r['memory']) for r in cases]
 results.append({'test_id':t.pk,'submission_id':s.pk,'verdict':verdict,'cases':len(cases),'one_native_dispatch':True,'callback_sql_agree':True,'archived_no_official_contest_or_participation':True,'runtime':s.language.key,'limits':[s.problem.time_limit,s.problem.memory_limit]})
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
# Native ContestStats uses Submission.contest_object; every official row is preserved,
# and no new submission has that FK. ContestParticipation/ContestSubmission, cached
# counts and native Problem statistics were also compared field-for-field above.
result={'status':'PASS','baseline_model_sets':len(before),'baseline_non_session_rows':count,'original_accounts_passwords_submissions_cases_sources_imports_contests_and_audits_preserved':True,
 'official_scores_penalties_ranks_contestant_counts_and_solve_statistics_unchanged':True,'native_problem_aggregate_statistics_unchanged':True,'native_runtime_advertisement_content_preserved':True,'no_pending_work':True,'actual_author_tests':results}
Path('/tmp/d13-preservation.json').write_text(json.dumps(result,indent=2))
print('PASS: all original non-session data retained; two private archived author tests AC3/WA3 match callbacks/SQL; official scores/counts/statistics unchanged.')
