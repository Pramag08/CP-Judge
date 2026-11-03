"""Delete only keys recovered from this run's private diagnostic-session logs."""
import importlib
import json
from django.conf import settings
from django.contrib.sessions.models import Session

backend = importlib.import_module(settings.SESSION_ENGINE)
for key in KEYS:
    store = backend.SessionStore(session_key=key)
    store.delete()
    assert store.load() == {}
assert not Session.objects.filter(session_key__in=KEYS).exists()
print('OPERATOR_RESULT=' + json.dumps({'status': 'PASS', 'owned_diagnostic_keys_cleared': len(KEYS),
      'database_and_cache_deleted': True, 'existing_sessions_untouched': True}))
