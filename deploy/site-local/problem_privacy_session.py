"""Mint only an ephemeral native participant session without touching the user."""
import importlib
import json
import os
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User

user = User.objects.filter(is_staff=False, is_superuser=False, is_active=True).order_by('pk').first()
assert user is not None and not user.has_perm('judge.edit_all_problem') and not user.has_perm('judge.see_private_problem')
assert not Path('/tmp/b05-privacy-session.json').exists(), 'Remove only a known stale diagnostic session before retry'
store = importlib.import_module(settings.SESSION_ENGINE).SessionStore()
store['_auth_user_id'] = str(user.pk)
store['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
store['_auth_user_hash'] = user.get_session_auth_hash()
store.set_expiry(300)
store.save()
data = {'key': store.session_key, 'cookie_name': settings.SESSION_COOKIE_NAME}
fd = os.open('/tmp/b05-privacy-session.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
os.write(fd, json.dumps(data).encode()); os.close(fd)
print('OPERATOR_RESULT=' + json.dumps(data))
