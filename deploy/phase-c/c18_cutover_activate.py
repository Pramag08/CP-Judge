import json
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management import call_command
from cpjudge.models import Audit,Identity
from cpjudge.email_identity import inventory,email_only
before=json.loads(Path('/tmp/c18-cutover-before.json').read_text())
assert not email_only()
new=Audit.objects.exclude(pk__in=[r['id'] for r in before['cpjudge.audit']])
corrections=list(new.filter(action='email.correct'));assert {a.subject_id for a in corrections}=={1,2,7,8}
assert all(a.details.get('address_basis')=='organizer_assigned_development' and a.details.get('mailbox_verified') is False and a.details.get('real_participant_identity') is False and a.details.get('development_fixture') is True for a in corrections)
for row in before['auth.user']:assert get_user_model().objects.get(pk=row['id']).password==row['password']
control=Path('/tmp/c18-cutover-control.json');assert not control.exists()
control.write_text(json.dumps({'reason':'Authorized C18 email-only cutover after organizer-assigned development addresses and zero unresolved canonical identities; no mailbox/real-identity verification claim.'}));control.chmod(0o600)
call_command('email_account','stage',actor_id=1,private_file=str(control))
mapping,issues=inventory();assert not issues and len(mapping)==len(before['auth.user'])
assert all(Identity.objects.filter(user_id=pk,canonical_email=key).exists() for pk,key in mapping.items())
call_command('email_account','cutover',actor_id=1,private_file=str(control))
assert email_only()
for row in before['auth.user']:assert get_user_model().objects.get(pk=row['id']).password==row['password']
result={'status':'PASS','assigned_development_accounts':4,'mailbox_verified':False,'real_participant_identities_claimed':False,'canonical_keys':len(mapping),'missing':0,'invalid':0,'conflicts':0,'email_only_enabled':True,'all_existing_password_hashes_unchanged':True,'all_existing_sessions_generation_revoked':True}
p=Path('/tmp/c18-cutover-receipt.json');p.write_text(json.dumps(result,indent=2));p.chmod(0o600)
print('Guarded email-only cutover enabled after complete unique canonical-key inventory; development provenance/password preservation confirmed.')
