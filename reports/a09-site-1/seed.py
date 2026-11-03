import json, os, platform, sys
from importlib.metadata import version
from django.contrib.auth.models import User
from django.db import connection
from django.core.cache import cache
from judge.models import Language, Profile, Judge, RuntimeVersion
lang, created = Language.objects.update_or_create(key='CPP23', defaults=dict(name='GNU C++23', short_name='C++23', common_name='C++', ace='c_cpp', pygments='cpp', extension='cpp'))
lang.full_clean()
user, created=User.objects.get_or_create(username='a09-smoke', defaults={'email':'a09-smoke@example.invalid'})
user.set_password(os.environ['A09_LOGIN_PASSWORD']); user.save()
profile, created=Profile.objects.get_or_create(user=user)
profile.language=lang; profile.save()
cache.set('a09:probe','isolated-cache-ok',30)
assert cache.get('a09:probe')=='isolated-cache-ok'
assert not Judge.objects.exists() and not RuntimeVersion.objects.exists()
with connection.cursor() as c:
    c.execute('SELECT VERSION()'); db=c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM django_migrations'); migrations=c.fetchone()[0]
print(json.dumps({'python':platform.python_version(),'django':version('Django'),'mysqlclient':version('mysqlclient'),'celery':version('celery'),'database':db,'applied_migrations':migrations,'language':{'key':lang.key,'name':lang.name,'default_profile_language':profile.language.key,'runtime_versions':lang.runtime_versions()},'judge_rows':Judge.objects.count(),'runtime_rows':RuntimeVersion.objects.count(),'cache':'PASS'},indent=2))
