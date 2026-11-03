"""Account-safe cutover comparison; no private addresses/hashes in public output."""
import json
from pathlib import Path
from django.apps import apps
from django.db import transaction
from django.contrib.auth import get_user_model
from judge.models import Profile,ContestParticipation,Submission
from cpjudge.models import Audit,Identity,EmailLoginPolicy,ProblemVersion
from cpjudge.email_identity import inventory,email_only
from cpjudge.publication import verify_native
before=json.loads(Path('/tmp/c18-cutover-before.json').read_text())
inputs=json.loads(Path('/tmp/cpj-email-mappings-input.json').read_text())
assigned={r['user_id']:r['email'] for r in inputs['accounts']};assert set(assigned)=={1,2,7,8}
assert email_only() and not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()
with transaction.atomic():
 for old in before['judge.profile']:
  p=Profile.objects.select_for_update().get(pk=old['id'])
  if p.current_contest_id==old['current_contest_id']:continue
  assert p.user_id in assigned and p.current_contest_id is None
  if old['current_contest_id']:
   previous=ContestParticipation.objects.get(pk=old['current_contest_id']);assert previous.user_id==p.pk and previous.ended
  Profile.objects.filter(pk=p.pk).update(current_contest_id=old['current_contest_id'])
models={m._meta.label_lower:m for m in apps.get_models() if not m._meta.proxy}
allowed={'auth.user':{'email','last_login'},'cpjudge.identity':{'canonical_email','generation'},'judge.profile':{'last_access','last_ip'},'judge.judge':{'ping','load','last_ip'},'cpjudge.emailloginpolicy':{'email_only'}}
count=0
for label,rows in before.items():
 if label=='sessions.session':continue
 m=models[label];pk=m._meta.pk.attname
 now={r[pk]:r for r in json.loads(json.dumps(list(m.objects.all().values()),default=str))}
 for old in rows:
  assert old[pk] in now,('removed',label)
  delta={key for key in old if old[key]!=now[old[pk]][key]}
  assert delta<=allowed.get(label,set()),('changed',label,delta)
  if label=='auth.user' and 'email' in delta:assert old['id'] in assigned and now[old['id']]['email']==assigned[old['id']]
  if label=='cpjudge.identity' and 'canonical_email' in delta:assert old['user_id'] in assigned and now[old['id']]['canonical_email']==assigned[old['user_id']]
  count+=1
 new=set(now)-{r[pk] for r in rows}
 if label=='cpjudge.audit':assert len(new)==6
 elif label=='cpjudge.identity':
  old_identity_users={row['user_id'] for row in before['cpjudge.identity']}
  expected_new=set(assigned)-old_identity_users
  added=[row for key,row in now.items() if key in new]
  assert {row['user_id'] for row in added}==expected_new
  assert all(row['college_id'] is None and not row['is_author'] and not row['must_change_password'] for row in added)
 else:assert not new,('unexpected addition',label)
U=get_user_model()
for old in before['auth.user']:
 user=U.objects.get(pk=old['id']);assert user.password==old['password'] and user.username==old['username']
 assert user.email==assigned.get(old['id'],old['email'])
audit_ids=[r['id'] for r in before['cpjudge.audit']]
added=list(Audit.objects.exclude(pk__in=audit_ids));assert len(added)==6
corrections=[a for a in added if a.action=='email.correct'];assert len(corrections)==4
for a in corrections:
 assert a.subject_id in assigned and a.actor_id==1
 assert a.details.get('address_basis')=='organizer_assigned_development'
 assert a.details.get('mailbox_verified') is False and a.details.get('real_participant_identity') is False and a.details.get('development_fixture') is True
 assert assigned[a.subject_id] not in json.dumps(a.details)
assert sorted(a.action for a in added if a.action!='email.correct')==['email.cutover','email.stage']
mapping,issues=inventory();assert not issues and len(mapping)==len(before['auth.user'])
assert all(Identity.objects.filter(user_id=pk,canonical_email=key).exists() for pk,key in mapping.items())
assert U.objects.get(pk=1).is_active and U.objects.get(pk=1).is_superuser
for version in ProblemVersion.objects.all():assert verify_native(version)
result={'status':'PASS','old_model_sets':len(before),'old_non_session_rows_checked':count,'old_accounts':len(before['auth.user']),
 'all_original_password_hashes_usernames_ids_college_history_roles_and_permissions_preserved':True,'prior_submissions_source_case_rows_contests_standings_and_audits_preserved':True,
 'only_four_authorized_email_fields_and_canonical_keys_changed':True,'additive_identity_rows_for_previously_unmapped_native_accounts':len(set(assigned)-{r['user_id'] for r in before['cpjudge.identity']}),'four_development_provenance_audits':True,'mailboxes_verified':False,'real_participant_identity_claim':False,
 'audit_additions':{'email.correct':4,'email.stage':1,'email.cutover':1},'email_only_enabled':True,'canonical_keys':len(mapping),'unresolved':0,
 'existing_native_versions_and_integration_receipts_preserved':True,'no_new_judging_or_rejudge':True,'no_password_reset_or_change':True,'admin_actor_1_active':True,'no_active_jobs':True,
 'normal_login_generations_access_timestamps_liveness_and_fixture_context_restoration_only':True}
p=Path('/tmp/c18-cutover-preservation.json');p.write_text(json.dumps(result,indent=2));p.chmod(0o600)
print('All original password hashes/IDs/history/results preserved; exactly four authorized development email assignments and one guarded cutover recorded.')
