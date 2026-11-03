"""Isolated browser acceptance database and port; never used by live Phase B."""
from dmoj.cpj_test_settings import *
DATABASES['default']['NAME'] = 'test_cpj_phase_c'
LOGIN_REDIRECT_URL = '/protected/'
EVENT_DAEMON_USE = False
