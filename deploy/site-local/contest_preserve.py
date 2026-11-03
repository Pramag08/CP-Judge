"""Compare only pre-existing rows; all test additions must belong to this fixture."""
import datetime,json
from pathlib import Path
from django.apps import apps
from judge.models import Contest,Submission
before=json.loads(Path('/tmp/b10-b11-before.json').read_text())
c=Contest.objects.get(key='b10b11local1')
added={}
for model in apps.get_models(include_auto_created=True):
 name=model._meta.label_lower
 if name=='judge.runtimeversion':continue
 rows=list(model.objects.order_by('pk').values())
 if name=='judge.judge':
  for r in rows:
   for k in ('online','ping','load','start_time','last_ip'):r.pop(k)
 def encode(x):return x.isoformat() if isinstance(x,(datetime.datetime,datetime.date,datetime.time)) else str(x)
 rows=json.loads(json.dumps(rows,default=encode));pk=model._meta.pk.attname;current={r[pk]:r for r in rows}
 old=before[name]
 for a in old:
  b=current[a[pk]];fields={k for k in a if a[k]!=b[k]}
  if name=='auth.user':assert fields<= {'last_login'}
  elif name=='judge.profile':assert fields<= {'last_access','ip'}
  elif name=='judge.problem':assert fields<= {'user_count','ac_rate'}
  else:assert not fields,(name,fields)
 count=len(rows)-len(old)
 if count:added[name]=count
assert added=={'auth.user':2,'judge.profile':2,'judge.contest':1,'judge.contest_private_contestants':2,
 'judge.contestparticipation':2,'judge.contestproblem':1,'judge.submission':6,'judge.submissionsource':6,
 'judge.submissiontestcase':515,'judge.contestsubmission':6},added
assert list(c.private_contestants.values_list('user__username',flat=True).order_by('user__username'))==['b10tmpa','b10tmpb']
assert c.time_limit is None and not c.is_rated and c.is_private
subs=Submission.objects.filter(contest_object=c)
assert subs.count()==6 and not subs.exclude(user__user__username__in=['b10tmpa','b10tmpb']).exists()
assert not subs.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
assert not c.problems.get().is_public
print('JOURNEY_RESULT='+json.dumps({'status':'PASS','models':len(before),'native_fixture_additions':added,
 'existing_accounts_passwords_submissions_problem_data_preserved':True,'allowed_existing_activity':'native login/access and problem statistics only',
 'immutable_problem_and_container_configuration_checked_by_coordinator':True}))
