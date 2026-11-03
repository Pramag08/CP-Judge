"""Native checkpoint tests only; live activation uses native_settings.py directly."""
from dmoj.settings import *
if not globals().get('CPJ_NATIVE', False):
    exec(open('/app/dmoj/cpj_native_settings.py').read())
DATABASES['default']['TEST']={'NAME':'test_cpj_phase_c'}
CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}}
PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher']
