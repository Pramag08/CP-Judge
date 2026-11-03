# Native services, private coordinator loopback only. No judge enrollment.
CELERY_BROKER_URL = 'redis://redis:6379/1'
CELERY_RESULT_BACKEND = 'redis://redis:6379/2'
BRIDGED_JUDGE_ADDRESS = [('127.0.0.1', 9999)]
BRIDGED_DJANGO_ADDRESS = [('127.0.0.1', 9998)]
BRIDGED_DJANGO_CONNECT = ('127.0.0.1', 9998)
EVENT_DAEMON_USE = True
EVENT_DAEMON_POST = 'ws://events:9997/'
EVENT_DAEMON_GET = 'ws://127.0.0.1:9996/'
EVENT_DAEMON_POLL = 'http://127.0.0.1:9995/channels/'
EVENT_DAEMON_KEY = None  # Native pinned daemon has no auth command; loopback isolation required.
