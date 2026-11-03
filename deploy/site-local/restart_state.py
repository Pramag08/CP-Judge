"""B12 precise pre-existing row comparison; no result or credential writes."""
import datetime,json
from pathlib import Path
from django.apps import apps
from judge.models import Submission
before=json.loads(Path('/tmp/b12-before.json').read_text())
additions={}
for model in apps.get_models(include_auto_created=True):
 name=model._meta.label_lower
 if name=='judge.runtimeversion':continue  # Bridge-owned transient version rows.
 rows=list(model.objects.order_by('pk').values())
 if name=='judge.judge':
  for row in rows:
   for key in ('online','ping','load','start_time','last_ip'):row.pop(key)
 def encode(value):return value.isoformat() if isinstance(value,(datetime.datetime,datetime.date,datetime.time)) else str(value)
 rows=json.loads(json.dumps(rows,default=encode));old=before[name]
 if name=='judge.judge_problems':
  assert sorted((r['judge_id'],r['problem_id']) for r in rows)==sorted((r['judge_id'],r['problem_id']) for r in old)
  continue
 pk=model._meta.pk.attname;current={r[pk]:r for r in rows}
 for a in old:
  b=current[a[pk]];fields={key for key in a if a[key]!=b[key]}
  if name=='auth.user':assert fields<={'last_login'},(name,fields)
  elif name=='judge.profile':assert fields<={'last_access','ip'},(name,fields)
  elif name=='judge.problem':assert fields<={'user_count','ac_rate'},(name,fields)
  else:assert not fields,(name,fields)
 count=len(rows)-len(old)
 if count:additions[name]=count
expected={} if MODE=='restarted' else {'judge.submission':1,'judge.submissionsource':1,'judge.submissiontestcase':103,'judge.contestsubmission':1}
assert additions==expected,additions
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
print('JOURNEY_RESULT='+json.dumps({'status':'PASS','mode':MODE,'models':len(before),'preserved_submissions':len(before['judge.submission']),'preserved_testcase_rows':len(before['judge.submissiontestcase']),'expected_new_rows':additions,
 'existing_credentials_hashes_contest_submissions_all_case_rows_and_standings_preserved':True,
 'allowed_activity':'native login/access and native problem statistics; bridge-owned transient state excluded',
 'interrupted_submission_recovery':'NOT TESTED; no in-progress jobs during stop'}))
