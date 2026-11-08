# Live checkpoint 1 overlay. Never import test_settings or browser_settings here.
INSTALLED_APPS += ('cpjudge.apps.CPJudgeConfig',)
CPJ_NATIVE = True
AUTHENTICATION_BACKENDS = ('cpjudge.identity.CollegeBackend',)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
# Preserve existing strong hashes and avoid opportunistic rehashing old passwords.
# New provision/reset/change credentials use Django PBKDF2 with its default work factor.
PASSWORD_HASHERS = ('django.contrib.auth.hashers.PBKDF2PasswordHasher',
                   'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
                   'django.contrib.auth.hashers.Argon2PasswordHasher',
                   'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
                   'django.contrib.auth.hashers.ScryptPasswordHasher')
MIDDLEWARE = [m for m in MIDDLEWARE if m not in (
    'judge.middleware.ShortCircuitMiddleware', 'judge.middleware.APIMiddleware',
    'impersonate.middleware.ImpersonateMiddleware', 'judge.middleware.DMOJImpersonationMiddleware')]
MIDDLEWARE.insert(MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware')+1,
                  'cpjudge.sessions.GenerationMiddleware')
MIDDLEWARE.append('cpjudge.uploads.UploadBoundaryMiddleware')
MIDDLEWARE.append('cpjudge.native.NativePolicyMiddleware')
ROOT_URLCONF = 'cpjudge.urls'
SITE_NAME = 'foobar'
SITE_LONG_NAME = 'foobar'
if 'WPADMIN' in globals():
    WPADMIN['admin']['title'] = 'foobar'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/contests/'
REGISTRATION_OPEN = False
DMOJ_ENABLE_SOCIAL = False
DMOJ_USER_DATA_DOWNLOAD = False  # Native unscoped archive tasks replaced by scoped roster jobs.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
# Local HTTP baseline only. Secure cookies require HTTPS on a future deployment.
CPJ_COLLEGE_ID_PATTERN = r'[A-Z0-9][A-Z0-9_-]{0,63}'
# Private upload storage and compressed single-package ceiling. Never point at
# STATIC_ROOT or MEDIA_ROOT; imports.private_root checks this at runtime too.
CPJ_IMPORT_ROOT = '/app/private-cpj-imports'
# One original Polygon package: 110.1 MiB compressed, 236.0 MiB expanded;
# the converter's inner native ZIP contains a 107.7 MiB data.zip member.
# Keep finite independent ceilings for compressed, member and total bytes.
CPJ_ARCHIVE_LIMITS = {'upload_bytes': 128 * 1024**2, 'entries': 1024,
                      'member_bytes': 128 * 1024**2, 'expanded_bytes': 320 * 1024**2,
                      'ratio': 1200}
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024**2
# Django's temporary upload is a mode-0600 file on the container's private /tmp
# disk; imports.upload streams it onward to the mode-0700 private import root.
FILE_UPLOAD_TEMP_DIR = '/tmp'
CPJ_UPLOAD_RESERVE_BYTES = 512 * 1024**2
CPJ_CONVERSION_MIN_FREE_BYTES = 2 * 1024**3
CPJ_CONVERSION_TIMEOUT = 600
CPJ_CONVERSION_MEMORY_BYTES = 1536 * 1024**2
CPJ_CONVERSION_CPU_SECONDS = 480
CPJ_CONVERSION_FILE_BYTES = 384 * 1024**2
CPJ_CONVERSION_QUEUE_TTL = 300
CPJ_CONVERSION_RUNNING_TTL = 660
CPJ_PUBLICATION_RESERVE_BYTES = 512 * 1024**2
EVENT_DAEMON_GET = ''
EVENT_DAEMON_POLL = '/cpjudge/events/'
# Internal native posting remains available; browsers never contact the daemon.
EVENT_DAEMON_USE = False  # Native results persist normally; authenticated DB polling supplies updates.
TEMPLATES[0]['DIRS'] = ['/app/cpjudge/templates', *TEMPLATES[0]['DIRS']]
TEMPLATES[0]['OPTIONS']['context_processors'].append('cpjudge.navigation.contest_navigation')
