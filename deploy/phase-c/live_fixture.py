"""Task-owned temporary native fixture; never touch existing credentials/grants."""
import datetime,json,os
from pathlib import Path
from django.contrib.auth import get_user_model
from django.utils import timezone
from judge.models import Contest,ContestProblem,ContestParticipation,Problem
from cpjudge.identity import provision
from cpjudge.policy import grant_scope
from cpjudge.models import Audit
U=get_user_model()
actor=U.objects.filter(is_active=True,is_superuser=True).order_by('pk').first()
assert actor is not None
accounts={}
for role,cid,author in [('a','C1LIVEA',True),('b','C1LIVEB',True),('p','C1LIVEP',False),('q','C1LIVEQ',False),('admin','C1LIVEADMIN',False)]:
 assert not U.objects.filter(username=cid).exists(),'Inspect prior fixture; do not reseed'
 user,password=provision(actor,cid,first_name='Checkpoint',last_name=role,email=role+'@checkpoint.invalid',author=author)
 if role=='admin':
  user.is_staff=True;user.is_superuser=True;user.save(update_fields=['is_staff','is_superuser'])
  Audit.objects.create(actor=actor,subject=user,action='fixture.admin')
 accounts[role]={'username':user.username,'password':password,'id':user.pk}
now=timezone.now()
contests={}
for role in ('a','b'):
 contest=Contest.objects.create(key='c1live'+role,name='Checkpoint 1 '+role.upper(),start_time=now-datetime.timedelta(hours=1),end_time=now+datetime.timedelta(hours=3),is_visible=True,is_private=True,format_name='cpjudge_icpc_v1',format_config={'penalty':20})
 for cap in ('settings.edit','roster.read','roster.export','submissions.review','source.review','grants.manage'):
  grant_scope(actor,U.objects.get(pk=accounts[role]['id']),contest,cap)
 contestant=U.objects.get(pk=accounts['p' if role=='a' else 'q']['id'])
 contest.private_contestants.add(contestant.profile)
 ContestParticipation.objects.create(contest=contest,user=contestant.profile)
 contests[role]={'id':contest.pk,'key':contest.key}
problem=Problem.objects.get(code='pv000000000000000001')
ContestProblem.objects.create(contest_id=contests['a']['id'],problem=problem,points=1,partial=False,order=0)
path=Path('/tmp/c1-live-accounts.json');assert not path.exists()
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
os.write(fd,json.dumps({'accounts':accounts,'contests':contests}).encode());os.close(fd)
print('Five task-owned native accounts and two private contests created; credentials saved privately.')
