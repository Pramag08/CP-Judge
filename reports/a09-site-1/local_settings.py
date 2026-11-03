# A09 disposable coordinator settings; not production configuration.
import os

SECRET_KEY = os.environ['A09_SECRET_KEY']
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'site', 'testserver']
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.mysql', 'NAME': os.environ.get('DB_NAME', 'a09'),
    'USER': os.environ.get('DB_USER', 'a09'), 'PASSWORD': os.environ['DB_PASSWORD'],
    'HOST': os.environ.get('DB_HOST', 'db'), 'PORT': '3306',
    'OPTIONS': {'charset': 'utf8mb4', 'connect_timeout': 3,
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'"},
}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': 'redis://redis:6379/0'}}
CELERY_BROKER_URL = 'redis://redis:6379/1'
CELERY_RESULT_BACKEND = 'redis://redis:6379/2'
COMPRESS_OUTPUT_DIR = 'cache'
STATICFILES_FINDERS += ('compressor.finders.CompressorFinder',)
STATIC_ROOT = '/app/static'
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
