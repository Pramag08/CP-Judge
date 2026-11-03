# Local-only B01 settings layered over the pinned upstream defaults.
import os

SECRET_KEY = os.environ['B01_SECRET_KEY']
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'site', 'testserver']
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.mysql', 'NAME': 'b01', 'USER': 'b01',
    'PASSWORD': os.environ['DB_PASSWORD'], 'HOST': 'db', 'PORT': '3306',
    'OPTIONS': {'charset': 'utf8mb4', 'connect_timeout': 3,
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'"},
}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                       'LOCATION': 'redis://redis:6379/0'}}
STATIC_ROOT = '/app/static'
COMPRESS_OUTPUT_DIR = 'cache'
STATICFILES_FINDERS += ('compressor.finders.CompressorFinder',)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
INLINE_JQUERY = False
JQUERY_JS = '/static/a09/jquery.min.js'
INLINE_FONTAWESOME = True
ACE_URL = '/static/a09/ace'
SELECT2_JS_URL = '/static/libs/select2/select2.js'
SELECT2_CSS_URL = '/static/libs/select2/select2.css'
EVENT_DAEMON_USE = False
DEFAULT_USER_LANGUAGE = 'CPP23'
DMOJ_CANONICAL = 'localhost'
DMOJ_SSL = 0
DMOJ_ENABLE_SOCIAL = False
REGISTRATION_OPEN = False
