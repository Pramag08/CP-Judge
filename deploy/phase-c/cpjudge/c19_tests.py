"""No forced changes, explicit organizer recovery and C17 admission regressions."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import close_old_connections
from django.test import TransactionTestCase,Client
from cpjudge.models import Identity,Audit
from cpjudge.identity import reset_account
from cpjudge.email_identity import provision_email
U=get_user_model()

class PasswordPolicyTests(TransactionTestCase):
 def setUp(self):
  cache.clear();self.admin=U.objects.create_superuser('reset-operator',email='operator@example.invalid',password='Operator-pass-17!')
  from judge.models import Profile
  Profile.objects.get_or_create(user=self.admin)
  self.user,self.password=provision_email(self.admin,'participant@example.invalid')
 def login(self,c=None,password=None):
  c=c or Client();r=c.post('/accounts/login/',{'username':self.user.email,'password':password or self.password})
  self.assertEqual(r.status_code,302);self.assertNotIn('/password/change',r.url);return c
 def test_first_login_and_historical_flag_do_not_force_change(self):
  original=self.user.password
  self.assertFalse(Identity.objects.get(user=self.user).must_change_password)
  Identity.objects.filter(user=self.user).update(must_change_password=True)
  c=self.login();self.assertEqual(c.get('/edit/profile/').status_code,200)
  self.user.refresh_from_db();self.assertEqual(self.user.password,original)
  self.assertContains(c.get('/edit/profile/'),'Change password (optional)')
 def test_verified_reset_revokes_stale_reads_posts_polling_and_password(self):
  clients=[self.login(Client()) for _ in range(3)]
  # Clone the current valid session to exercise distinct first stale requests.
  import copy
  old=self.login();clones=[]
  for _ in range(3):
   c=Client();c.cookies=copy.deepcopy(old.cookies);clones.append(c)
  user,password=reset_account(self.admin,self.user.pk,reason='Verified fixture recovery',requester_verified=True)
  self.assertFalse(Identity.objects.get(user=user).must_change_password)
  self.assertFalse(user.check_password(self.password));self.assertTrue(user.check_password(password))
  self.assertEqual(clones[0].get('/edit/profile/').status_code,401)
  self.assertEqual(clones[1].post('/edit/profile/',{'first_name':'stale'}).status_code,401)
  self.assertEqual(clones[2].get('/cpjudge/events/submissions').status_code,401)
  self.login(password=password)
  audit=Audit.objects.get(action='account.reset',subject=user)
  self.assertNotIn(password,str(audit.details));self.assertNotIn(user.password,str(audit.details))
  self.assertEqual(audit.actor_id,self.admin.pk)
 def test_unverified_unauthorized_and_reasonless_resets_rejected(self):
  for actor,reason,verified,error in ((self.user,'reason',True,PermissionDenied),(self.admin,'reason',False,ValidationError),(self.admin,'',True,ValidationError)):
   with self.assertRaises(error):reset_account(actor,self.user.pk,reason=reason,requester_verified=verified)
  self.user.refresh_from_db();self.assertTrue(self.user.check_password(self.password));self.assertFalse(Audit.objects.filter(action='account.reset').exists())
 def test_optional_change_rotates_current_session_and_logout_does_not_revoke_replacement(self):
  old=self.login();current=self.login()
  self.assertEqual(old.post('/accounts/logout/').status_code,401)
  self.assertEqual(current.get('/edit/profile/').status_code,200)
  r=current.post('/accounts/password/change/',{'old_password':self.password,'new_password1':'Voluntary-change-92!','new_password2':'Voluntary-change-92!'})
  self.assertEqual(r.status_code,302);self.assertEqual(current.get('/edit/profile/').status_code,200)
  self.user.refresh_from_db();self.assertTrue(self.user.check_password('Voluntary-change-92!'))
  self.assertTrue(Audit.objects.filter(action='password.change',subject=self.user).exists())
 def test_simultaneous_email_logins_leave_one_active_generation(self):
  barrier=Barrier(2)
  def run(_):
   close_old_connections()
   try:
    c=Client();barrier.wait(10);r=c.post('/accounts/login/',{'username':self.user.email,'password':self.password});return c,r.status_code
   finally:close_old_connections()
  with ThreadPoolExecutor(2) as pool:rows=list(pool.map(run,range(2)))
  self.assertEqual([status for c,status in rows],[302,302])
  self.assertCountEqual([c.get('/cpjudge/events/submissions').status_code for c,status in rows],[200,401])
 def test_disable_and_recovery_have_no_email_token_service(self):
  c=self.login();U.objects.filter(pk=self.user.pk).update(is_active=False)
  self.assertIn(c.get('/edit/profile/').status_code,(401,403))
  with patch('django.core.mail.send_mail') as mail:
   response=Client().get('/accounts/password/reset/');self.assertContains(response,'outside this application');mail.assert_not_called()
  for path in ('/accounts/password/reset/done/','/accounts/password/reset/confirm/token/','/accounts/register/'):
   self.assertIn(Client().get(path).status_code,(401,403,404))
