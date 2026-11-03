"""Only clearly named B10/B11 temporary users and one private native contest."""
import datetime,json
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from judge.models import Contest,ContestProblem,Profile,Problem,Language
with transaction.atomic():
 assert not Contest.objects.filter(key='b10b11local1').exists()
 profiles=[]
 for data in ACCOUNTS.values():
  assert not User.objects.filter(username=data['username']).exists()
  u=User.objects.create_user(**data,is_staff=False,is_superuser=False,is_active=True)
  p=Profile.objects.create(user=u,language=Language.objects.get(key='CPP23'))
  assert not u.get_all_permissions();profiles.append(p)
 now=timezone.now()
 c=Contest.objects.create(key='b10b11local1',name='TEMP B10 B11 individual acceptance',description='Temporary operator test fixture; two ordinary individual entrants. Not an event deployment.',
  start_time=now-datetime.timedelta(minutes=2),end_time=now+datetime.timedelta(hours=2),time_limit=None,
  is_visible=True,is_private=True,is_rated=False,format_name='icpc',format_config={'penalty':20},points_precision=0,show_short_display=True)
 c.private_contestants.set(profiles)
 p=Problem.objects.get(code='pv000000000000000001');assert not p.is_public
 cp=ContestProblem.objects.create(contest=c,problem=p,points=1,partial=False,order=0)
 result={'contest_id':c.pk,'key':c.key,'start':c.start_time.isoformat(),'end':c.end_time.isoformat(),
         'temporary_accounts':[p.user.username for p in profiles],'native_contest_problem':cp.pk,
         'private_allowlist_only':True,'per_participant_duration':None,'fixture_start_two_minutes_before_creation':True}
print('JOURNEY_RESULT='+json.dumps(result))
