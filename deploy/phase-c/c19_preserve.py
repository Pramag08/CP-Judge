"""Private all-model baseline comparison and actual judging continuity."""
import hashlib,json
from pathlib import Path
from django.apps import apps
from django.db import transaction
from judge.models import Submission,ContestSubmission,ContestParticipation,Profile,Judge
from cpjudge.models import ProblemProbe,ProblemVersion,Identity,EmailLoginPolicy,Audit
from cpjudge.publication import verify_native
from cpjudge.probes import binding
before=json.loads(Path('/tmp/c13-identity-before.json').read_text())
assert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
assert Judge.objects.get(name='cpjudge-local-worker').online
assert not EmailLoginPolicy.objects.filter(email_only=True).exists()
with transaction.atomic():
 for old in before['judge.profile']:
  p=Profile.objects.select_for_update().get(pk=old['id'])
  if p.current_contest_id==old['current_contest_id']:continue
  assert p.user.username in ('C1LIVEA','C1LIVEB','C1LIVEP')
  if old['current_contest_id']:
   previous=ContestParticipation.objects.get(pk=old['current_contest_id']);assert previous.user_id==p.pk and previous.ended
  if p.current_contest_id:
   from django.utils import timezone
   current=p.current_contest
   assert current.user_id==p.pk and (current.virtual==-1 or current.virtual>0) and current.contest.end_time<timezone.now()
   assert current.pk not in {r['id'] for r in before['judge.contestparticipation']}
   assert ContestSubmission.objects.filter(participation=current,submission__problem__code='pv000000000000000001').exists()
  Profile.objects.filter(pk=p.pk).update(current_contest_id=old['current_contest_id'])
models={m._meta.label_lower:m for m in apps.get_models() if not m._meta.proxy}
allowed={'auth.user':{'last_login'},'cpjudge.identity':{'generation'},'judge.profile':{'last_access','last_ip','ip'},'judge.judge':{'ping','load','last_ip','start_time','online'},'judge.problem':{'ac_rate','user_count'}}
count=0;changes={}
for label,oldrows in before.items():
 if label=='sessions.session':continue
 m=models[label];pk=m._meta.pk.attname
 if label=='judge.runtimeversion':
  now=json.loads(json.dumps(list(m.objects.all().values()),default=str))
  strip=lambda rows:sorted([dict(r,**{pk:None}) for r in rows],key=lambda r:json.dumps(r,sort_keys=True))
  assert strip(oldrows)==strip(now),'Native runtime versions changed'
  count+=len(oldrows);continue
 current={r[pk]:r for r in json.loads(json.dumps(list(m.objects.all().values()),default=str))}
 for old in oldrows:
  assert old[pk] in current,('removed',label,old[pk])
  delta={k for k in old if old[k]!=current[old[pk]][k]}
  assert delta<=allowed.get(label,set()),('changed',label,old[pk],delta)
  if delta:changes[label]=sorted(set(changes.get(label,[]))|delta)
  count+=1
for v in ProblemVersion.objects.all():assert verify_native(v)
probes=list(ProblemProbe.objects.all());assert len(probes)==2
for probe in probes:assert binding(probe)
oldids={r['id'] for r in before['judge.submission']}
new=list(Submission.objects.exclude(pk__in=oldids).exclude(private_probe__isnull=False));assert len(new)==1
s=new[0];cases=list(s.test_cases.all())
assert s.problem.code=='pv000000000000000001' and s.language.key=='CPP23' and s.status=='D' and s.result=='AC'
assert len(cases)==103 and all(c.status=='AC' and c.points==c.total==1 for c in cases)
trace=[json.loads(l) for l in Path('/tmp/c11-native-trace.jsonl').read_text().splitlines()]
packets=[r for r in trace if r.get('submission-id')==s.pk and r['direction']=='sent' and r['name']=='submission-request']
assert len(packets)==1 and packets[0]['language']=='CPP23' and packets[0]['time-limit']==2 and packets[0]['memory-limit']==262144
callbacks=[c for r in trace if r.get('submission-id')==s.pk and r['direction']=='received-and-handled' and r['name']=='test-case-status' for c in r['cases']]
assert len(callbacks)==103 and all(c['status']==0 for c in callbacks)
# No probe acquired official associations or participant visibility.
for probe in probes:
 assert not ContestSubmission.objects.filter(submission_id=probe.execution_id).exists()
 assert not probe.version.problem.is_public and not probe.version.problem.allowed_languages.exists()
# Original users' hashes/emails/IDs are exact, not just password checks.
assert all(get_user.password==row['password'] and get_user.email==row['email'] for row in before['auth.user'] for get_user in [models['auth.user'].objects.get(pk=row['id'])])
# Reset audits describe the synthetic account only, with actor/reason and no credential values.
newusers=models['auth.user'].objects.exclude(pk__in=[r['id'] for r in before['auth.user']]);assert newusers.count()==1
fixture=newusers.get();resets=Audit.objects.filter(subject=fixture,action='account.reset');assert resets.count()==2
assert all(a.details.get('requester_verification')=='administrator-attested-outside-app' for a in resets)
result={'status':'PASS','original_model_sets':len(before),'original_non_session_rows_checked':count,
 'original_account_ids_hashes_emails_and_college_history_preserved':True,'prior_submissions_case_rows_and_official_standings_preserved':True,
 'normal_native_activity_fields':changes,'expired_contest_profile_pointers_restored':True,
 'actual_private_probes':2,'synthetic_external_accounts_added':1,'synthetic_fixture_resets':2,
 'participant_submission':{'id':s.pk,'participation_mode':'native virtual practice in ended fixture contest','verdict':'AC','cases':103,'callback_cases':103,'native_dispatches':1,'runtime':'CPP23','time_seconds':2,'memory_kib':262144},
 'email_only_cutover':False,'missing_email_blockers':4,'current_worker_online':True,'native_runtime_values_preserved_across_reconnect_ids':True,'no_active_jobs':True,
 'same_import_probe_participant_standings_integration':'NOT TESTED; probe version differs from preserved participant fixture'}
p=Path('/tmp/c19-preservation.json');p.write_text(json.dumps(result,indent=2));p.chmod(0o600)
print('Existing accounts/passwords/emails/history/results/standings preserved; one real participant AC103/callback/native packet proof complete.')
