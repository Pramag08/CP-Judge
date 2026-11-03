import json,secrets
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management import call_command
from cpjudge.models import Identity
actor=get_user_model().objects.filter(is_active=True,is_superuser=True).order_by('pk').first();assert actor
inputfile=Path('/tmp/c19-provision-input.json');assert not inputfile.exists()
inputfile.write_text(json.dumps({'email':'acceptance-'+secrets.token_hex(10)+'@example.invalid','first_name':'Acceptance','last_name':'External'}));inputfile.chmod(0o600)
call_command('email_account','provision',actor_id=actor.pk,private_file=str(inputfile),output_file='/tmp/c19-new-account.json')
data=json.loads(Path('/tmp/c19-new-account.json').read_text());u=get_user_model().objects.get(pk=data['user_id'])
assert not Identity.objects.get(user=u).must_change_password
assert Identity.objects.get(user=u).college_id is None
assert not u.is_staff and not u.is_superuser
print('Authorized synthetic external acceptance fixture provisioned without college ID; private credential saved.')
