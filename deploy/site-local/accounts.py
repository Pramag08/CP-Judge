"""Explicit development provisioning/reset only; ordinary verification never calls it."""
import json
from pathlib import Path
from django.contrib.auth.models import User
from judge.models import Language, Profile

credentials=json.loads(Path(globals().get('ACCOUNT_FILE','/tmp/cpjudge-dev-accounts.json')).read_text())
reset=globals().get('RESET_PASSWORDS',False)
for role,data in credentials.items():
    if reset:
        user=User.objects.get(username=data['username'])
        user.set_password(data['password'])
        user.save(update_fields=['password'])
    else:
        assert not User.objects.filter(username=data['username']).exists(), 'Existing account requires explicit reset, never implicit reseeding'
        language,_=Language.objects.get_or_create(key='CPP23',defaults=dict(name='GNU C++23',short_name='C++23',common_name='C++',ace='c_cpp',pygments='cpp',extension='cpp'))
        user=User.objects.create_user(username=data['username'],password=data['password'],is_active=True,is_staff=role=='staff',is_superuser=role=='staff')
        profile,_=Profile.objects.get_or_create(user=user)
        profile.language=language;profile.save(update_fields=['language'])
    assert user.check_password(data['password'])
print(json.dumps({'mode':'explicit reset' if reset else 'initial creation','accounts':len(credentials),'password_checks':'PASS','roles_changed_on_reset':False}))
