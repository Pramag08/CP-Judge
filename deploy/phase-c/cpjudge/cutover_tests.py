"""Email-only admission, explicit development provenance and local recovery."""
import io,json,os,tempfile
from pathlib import Path
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TransactionTestCase,Client
from cpjudge.models import Identity,Audit
from cpjudge.email_identity import stage_keys,set_mode,correct_email,provision_email,email_only
from cpjudge.c19_tests import PasswordPolicyTests
U=get_user_model()

class CutoverTests(TransactionTestCase):
 def setUp(self):
  cache.clear();self.admin=U.objects.create_superuser('cutover-admin',email='staff@example.invalid',password='Existing-fixture-password-31!')
  from judge.models import Profile
  Profile.objects.get_or_create(user=self.admin)
  self.user,self.password=provision_email(self.admin,'participant@example.invalid')
  stage_keys(self.admin)
 def test_development_assignment_records_no_mailbox_or_real_identity_claim(self):
  old=self.user.password
  with patch('django.core.mail.send_mail') as mail:
   correct_email(self.admin,self.user.pk,self.user.email,'Organizer-assigned development fixture; not a verified mailbox or real person.',assignment_kind='organizer_assigned_development')
   mail.assert_not_called()
  self.user.refresh_from_db();self.assertEqual(self.user.password,old)
  data=Audit.objects.get(action='email.correct',subject=self.user).details
  self.assertEqual(data['address_basis'],'organizer_assigned_development')
  self.assertIs(data['development_fixture'],True);self.assertIs(data['mailbox_verified'],False);self.assertIs(data['real_participant_identity'],False)
 def test_ordinary_and_admin_routes_reject_username_accept_email_without_force(self):
  set_mode(self.admin,True,'Guarded isolated cutover')
  c=Client()
  for identifier in (self.admin.username,self.user.username):
   password='Existing-fixture-password-31!' if identifier==self.admin.username else self.password
   response=c.post('/accounts/login/',{'username':identifier,'password':password})
   self.assertEqual(response.status_code,200);self.assertNotIn('_auth_user_id',c.session)
  response=c.post('/admin/login/',{'username':self.admin.username,'password':'Existing-fixture-password-31!'})
  self.assertEqual(response.status_code,302);self.assertTrue(response.url.startswith('/accounts/login/'))
  self.assertNotIn('_auth_user_id',c.session)
  response=c.post('/accounts/login/',{'username':' STAFF@EXAMPLE.INVALID ','password':'Existing-fixture-password-31!','next':'/admin/'})
  self.assertEqual(response.status_code,302);self.assertEqual(response.url,'/admin/')
  self.assertEqual(c.get('/admin/auth/user/').status_code,200)
  self.assertEqual(c.get('/edit/profile/').status_code,200)
 def test_documented_local_rollback_restores_admin_username_without_password_reset(self):
  set_mode(self.admin,True,'Isolated rehearsal')
  extra,pw=provision_email(self.admin,'entrant-a@example.invalid')
  old={u.pk:u.password for u in U.objects.all()}
  marker=Audit.objects.create(actor=self.admin,subject=extra,action='test.retained')
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'reason.json';path.write_text(json.dumps({'reason':'Explicit local administrator recovery rehearsal; retain schema/data/passwords.'}));path.chmod(0o600)
   with patch('django.core.mail.send_mail') as mail:
    call_command('email_account','rollback',actor_id=self.admin.pk,private_file=str(path),stdout=io.StringIO());mail.assert_not_called()
   self.assertFalse(email_only());self.assertTrue(Audit.objects.filter(pk=marker.pk).exists())
   c=Client();self.assertEqual(c.post('/accounts/login/',{'username':self.admin.username,'password':'Existing-fixture-password-31!'}).status_code,302)
   self.assertEqual(c.get('/admin/auth/user/').status_code,200)
   self.assertEqual(c.post('/accounts/login/',{'username':extra.email,'password':pw}).status_code,302)
   call_command('email_account','cutover',actor_id=self.admin.pk,private_file=str(path),stdout=io.StringIO())
   self.assertTrue(email_only());self.assertEqual(c.get('/edit/profile/').status_code,401)
  for pk,password in old.items():self.assertEqual(U.objects.get(pk=pk).password,password)

class EmailOnlySessionTests(PasswordPolicyTests):
 def setUp(self):
  super().setUp();stage_keys(self.admin);set_mode(self.admin,True,'Email-only session regression')
