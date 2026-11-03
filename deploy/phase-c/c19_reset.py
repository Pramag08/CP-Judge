import json
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management import call_command
actor=get_user_model().objects.filter(is_active=True,is_superuser=True).order_by('pk').first()
data=json.loads(Path('/tmp/c19-new-account.json').read_text())
suffix=globals().get('C19_ATTEMPT','')
p=Path('/tmp/c19-reset-input'+suffix+'.json');assert not p.exists()
p.write_text(json.dumps({'user_id':data['user_id'],'reason':'Organizer verified task-owned synthetic acceptance requester','requester_verified':True}));p.chmod(0o600)
call_command('account_password_reset',actor_id=actor.pk,private_file=str(p),output_file='/tmp/c19-reset-account'+suffix+'.json')
