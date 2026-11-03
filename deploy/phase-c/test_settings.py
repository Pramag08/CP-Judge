"""Isolated Phase C acceptance settings. Never used by the live site."""
from dmoj.settings import *
INSTALLED_APPS += ('cpjudge.apps.CPJudgeConfig',)
AUTHENTICATION_BACKENDS = ('cpjudge.identity.CollegeBackend',)
AUTH_PASSWORD_VALIDATORS = [v for v in AUTH_PASSWORD_VALIDATORS if 'Pwned' not in v['NAME']]
MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware') + 1,
                  'cpjudge.sessions.GenerationMiddleware')
ROOT_URLCONF = 'cpjudge.test_urls'
DATABASES['default']['TEST'] = {'NAME':'test_cpj_phase_c'}
# Native middleware still requires Redis; test rate-limit keys use a separate cache.
CACHES = {'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
CPJ_IMPORT_ROOT = '/tmp/cpj-phase-c-import-tests'

import os
os.environ['PCC_ROOT'] = '/tmp/cpj-pcc'
