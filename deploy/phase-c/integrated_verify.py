"""Actual native SQL/callback/manual scoring and strict preservation proof."""
import hashlib,json,math
from pathlib import Path
from types import SimpleNamespace
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction
from judge.models import Submission,Contest,ContestSubmission,ContestParticipation,Profile,Judge
from judge.views.contests import get_contest_ranking_list
from cpjudge.models import ProblemVersion,ProblemProbe,ContestVersionAdmission
from cpjudge.publication import verify_native
from cpjudge.admission import verify_approval,validate_execution
from cpjudge.probes import binding
from cpjudge.email_identity import inventory,email_only
meta=json.loads(Path('/tmp/integrated-fixture.json').read_text());c=Contest.objects.get(pk=meta['contest_id'])
v=ProblemVersion.objects.get(pk=meta['version_id']);a=ContestVersionAdmission.objects.get(pk=meta['admission_id'])
assert verify_native(v) and verify_approval(a)
assert v.digest==meta['digest'] and v.manifest['package_sha256']==meta['package_sha256']
probe=ProblemProbe.objects.get(pk=meta['probe_id']);assert binding(probe)
assert probe.problem_digest==v.digest and probe.execution.result=='AC'
assert not ContestSubmission.objects.filter(submission=probe.execution).exists()
assert not v.problem.is_public
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
assert not email_only()
trace=[json.loads(line) for line in Path('/tmp/c11-native-trace.jsonl').read_text().splitlines()]
submissions=list(Submission.objects.filter(contest_object=c).order_by('pk'));assert len(submissions)==3
out=[]
for s,wanted in zip(submissions,['WA','AC','AC']):
 assert s.status=='D' and s.result==wanted and s.problem_id==v.problem_id and s.language.key=='CPP17'
 assert validate_execution(s).version_id==v.pk
 assert s.contest.participation.virtual==0
 cases=list(s.test_cases.order_by('case'));assert len(cases)==3 and all(row.status==wanted for row in cases)
 assert [row.case for row in cases]==[1,2,3]
 assert all(row.total==1 and row.points==(1 if wanted=='AC' else 0) for row in cases)
 sent=[r for r in trace if r.get('submission-id')==s.pk and r['direction']=='sent' and r['name']=='submission-request']
 assert len(sent)==1 and sent[0]['problem-id']==v.code and sent[0]['language']=='CPP17' and sent[0]['time-limit']==.5 and sent[0]['memory-limit']==65536
 callbacks=[case for r in trace if r.get('submission-id')==s.pk and r['direction']=='received-and-handled' and r['name']=='test-case-status' for case in r['cases']]
 assert len(callbacks)==3
 assert all(row['status']==(0 if wanted=='AC' else 1) for row in callbacks)
 out.append({'id':s.pk,'verdict':wanted,'cases':3,'callbacks':3,'packets':1,'native_code':s.problem.code,'runtime':'CPP17','participation':'LIVE/official'})
p,q=submissions[1],submissions[2]
assert submissions[0].user_id==p.user_id and q.user_id!=p.user_id
expected={p.user.user.username:{'solved':1,'penalty':math.floor((p.date-c.start_time).total_seconds())+1200,'failures':1,'elapsed':math.floor((p.date-c.start_time).total_seconds())},q.user.user.username:{'solved':1,'penalty':math.floor((q.date-c.start_time).total_seconds()),'failures':0,'elapsed':math.floor((q.date-c.start_time).total_seconds())}}
for entry in c.users.all():
 e=expected[entry.user.user.username]
 assert entry.virtual==0 and entry.score==e['solved'] and entry.cumtime==e['penalty'] and entry.tiebreaker==0
 data=entry.format_data[str(a.contest_problem_id)]
 assert data['points']==1 and data['penalty']==e['failures'] and data['time']==e['elapsed']
request=SimpleNamespace(user=p.user.user,profile=p.user)
ranked,_=get_contest_ranking_list(request,c,show_current_virtual=False)
ranks=[{'rank':rank,'username':person.username,'solved':person.points,'penalty':person.cumtime} for rank,person in ranked]
ordered=sorted(expected,key=lambda key:(-expected[key]['solved'],expected[key]['penalty']))
assert [row['username'] for row in ranks]==ordered
assert [row['rank'] for row in ranks]==[1,2]
# Restore only fixture navigation context, retaining all new official entries/results.
before=json.loads(Path('/tmp/integrated-before.json').read_text())
with transaction.atomic():
 for old in before['judge.profile']:
  profile=Profile.objects.select_for_update().get(pk=old['id'])
  if profile.current_contest_id==old['current_contest_id']:continue
  assert profile.user.username in ('C1LIVEA','C1LIVEB','C1LIVEP','C1LIVEQ')
  if profile.current_contest_id:assert profile.current_contest.contest_id==c.pk and profile.current_contest.user_id==profile.pk
  if old['current_contest_id']:
   previous=ContestParticipation.objects.get(pk=old['current_contest_id']);assert previous.user_id==profile.pk and previous.ended
  Profile.objects.filter(pk=profile.pk).update(current_contest_id=old['current_contest_id'])
models={m._meta.label_lower:m for m in apps.get_models() if not m._meta.proxy}
allowed={'auth.user':{'last_login'},'cpjudge.identity':{'generation'},'judge.profile':{'last_access','last_ip'},'judge.judge':{'start_time','online','ping','load','last_ip'},'judge.problem':{'ac_rate','user_count'}}
count=0
for label,rows in before.items():
 if label=='sessions.session':continue
 model=models[label];pk=model._meta.pk.attname;now=json.loads(json.dumps(list(model.objects.all().values()),default=str))
 if label=='judge.runtimeversion':
  strip=lambda data:sorted([dict(row,**{pk:None}) for row in data],key=lambda row:json.dumps(row,sort_keys=True))
  assert strip(rows)==strip(now);count+=len(rows);continue
 current={row[pk]:row for row in now}
 for old in rows:
  assert old[pk] in current,('removed',label)
  delta={key for key in old if old[key]!=current[old[pk]][key]}
  assert delta<=allowed.get(label,set()),('changed',label,delta)
  count+=1
for old in before['auth.user']:
 user=get_user_model().objects.get(pk=old['id'])
 assert user.password==old['password'] and user.email==old['email'] and user.username==old['username']
_,issues=inventory();assert [(row['user_id'],row['issue']) for row in issues]==[(1,'missing'),(2,'missing'),(7,'missing'),(8,'missing')]
result={'status':'PASS','same_version_chain':{'job_id':v.job_id,'conversion_attempt':v.attempt,'version_id':v.pk,'native_code':v.code,'version_digest':v.digest,'package_sha256':v.job.package_sha256,'accepted_probe':probe.pk,'probe_execution':probe.execution_id,'private_contest':c.key,'admission':a.pk},'runs':out,'expected':expected,'native_ranks':ranks,'old_model_sets':len(before),'old_non_session_rows_checked':count,'all_original_password_hashes_emails_ids_and_history_preserved':True,'prior_submissions_and_official_standings_preserved':True,'original_immutable_version_manifest_and_file_hashes_preserved':True,'four_missing_emails_unchanged':True,'email_only_enabled':False,'probe_has_no_official_association':True,'no_active_jobs':True,'worker_online':Judge.objects.get(name='cpjudge-local-worker').online}
path=Path('/tmp/integrated-proof.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
print('Actual same-version packets/callbacks/SQL and hand-calculated official standings agree; original accounts/passwords/emails/history/results preserved.')
