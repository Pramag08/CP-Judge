"""Additional isolated stock contest to exercise the second installed problem/language."""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from judge.models import Contest,ContestProblem,Problem
from django.contrib.auth import get_user_model
from cpjudge.contest_manage import FIXED
key='estock1';assert not Contest.objects.filter(key=key).exists()
p=Problem.objects.get(code='pv000000000000000001')
assert p.allowed_languages.filter(key='CPP23').exists()
u=get_user_model().objects.get(email='primary@e-accept.example.test')
with transaction.atomic():
 c=Contest.objects.create(key=key,name='E acceptance second problem and language',description='Temporary local development fixture.',start_time=timezone.now()-timedelta(minutes=5),end_time=timezone.now()+timedelta(hours=3),is_visible=True,**FIXED)
 ContestProblem.objects.create(contest=c,problem=p,order=0,points=1,partial=False)
 c.private_contestants.add(u.profile)
print('Created additive stock development contest with existing installed CPP23 problem.')
