"""D13 permission, immutable binding and score isolation; DB verdicts are constructed."""
import uuid
from unittest.mock import patch
from django.core.exceptions import PermissionDenied
from django.test import Client
from django.http import Http404
from judge.models import Submission,ContestSubmission,Contest,ContestParticipation
from cpjudge.entry_tests import EntryTests
from cpjudge import author_tests as t,entries as e
from cpjudge.models import AuthorTest,Identity,Grant,Conflict,ContestVersionAdmission
from cpjudge.native import review,visible_submissions
from cpjudge.policy import grant_scope

class AuthorTests(EntryTests):
 def setUp(self):
  super().setUp();self.path=f'/author/contests/{self.contest.key}/test/{self.v.code}/'
 def admit_test(self,user=None,key=None,source='int main(){}',language=None):
  user=user or self.owner
  return t.admit(user,self.contest.key,self.v.code,language or self.lang.pk,source,key or str(uuid.uuid4()),generation=Identity.objects.get(user=user).generation,auth_hash=user.get_session_auth_hash())
 def test_owner_scope_admin_and_participant_cannot_select_test_mode(self):
  for user in (self.p,self.q,self.admin):
   with self.assertRaises(PermissionDenied):t.authorize(user,self.contest)
  t.authorize(self.owner,self.contest)
  # Account administrator requires explicit contest content scopes.
  for cap in ('settings.edit','submissions.review'):grant_scope(self.admin,self.admin,self.contest,cap)
  t.authorize(self.admin,self.contest)
  for cap in ('settings.edit','submissions.review'):grant_scope(self.admin,self.q,self.contest,cap)
  with self.assertRaises(PermissionDenied):t.authorize(self.q,self.contest)
  owner=self.logged('C5A');participant=self.logged('C5P');other=self.logged('C5B')
  self.assertContains(owner.get(self.path),'Author preview / test mode')
  for client in (participant,other,Client()):
   for method in ('get','post'):
    self.assertIn(getattr(client,method)(self.path,{'language':self.lang.pk,'source':'int main(){}','request_key':str(uuid.uuid4()),'official':'true'}).status_code,(401,403,404))
  self.assertEqual(AuthorTest.objects.count(),0)
  # Scoped administrator can execute the same private machinery and preview assets.
  self.admin.email='scoped-admin@private.invalid';self.admin.save(update_fields=['email'])
  Identity.objects.update_or_create(user=self.admin,defaults={'canonical_email':self.admin.email})
  with patch('cpjudge.author_tests.dispatch'):
   execution,created=self.admit_test(self.admin)
  self.assertTrue(created);self.assertTrue(t.binding(execution))
  admin_client=Client();admin_client.force_login(self.admin,backend='cpjudge.identity.CollegeBackend')
  self.assertEqual(admin_client.get(self.path).status_code,200)
  self.assertEqual(admin_client.get('/problem/'+self.v.code).status_code,200)
  self.assertEqual(admin_client.get('/problem/'+self.v.code+'/published-assets/statement.css').status_code,200)
 def test_private_receipt_retry_native_poll_privacy_and_revocation(self):
  with patch('cpjudge.author_tests.dispatch') as dispatch:
   key=str(uuid.uuid4());s,created=self.admit_test(key=key)
   self.assertTrue(created);self.assertEqual(self.admit_test(key=key)[0].pk,s.pk);dispatch.assert_called_once()
   self.assertTrue(t.binding(s));self.assertTrue(s.is_archived);self.assertIsNone(s.contest_object_id)
   self.assertFalse(ContestSubmission.objects.filter(submission=s).exists())
   with self.assertRaises(PermissionDenied):self.admit_test(key=key,source='changed')
  for handle in ('C5A','C5P','C5B'):
   c=self.logged(handle)
   for path in (f'/submission/{s.pk}',f'/src/{s.pk}/raw',f'/widgets/submission_testcases?id={s.pk}',f'/cpjudge/events/sub_{s.id_secret}'):
    self.assertEqual(c.get(path).status_code,404)
   self.assertFalse(review(self.users[handle],s));self.assertFalse(visible_submissions(self.users[handle],Submission.objects.all()).filter(pk=s.pk).exists())
  grant_scope(self.admin,self.owner,self.contest,'settings.edit',revoke=True)
  with self.assertRaises(PermissionDenied):t.authorize(self.owner,self.contest)
  self.assertTrue(t.binding(s));self.assertTrue(Conflict.objects.filter(user=self.owner,contest=self.contest).exists())
 def test_scoring_counts_statistics_unchanged_by_constructed_ac_wa(self):
  with patch('cpjudge.entries.server_now',return_value=self.running),patch('cpjudge.entries.dispatch'):
   entry=self.register();official,_=self.submit()
  Submission.objects.filter(pk=official.pk).update(status='D',result='AC',case_points=3,case_total=3)
  official.refresh_from_db();official.update_contest();self.v.problem.update_stats()
  from judge.views.contests import get_contest_ranking_list
  from types import SimpleNamespace
  request=SimpleNamespace(user=self.owner,profile=self.owner.profile)
  def snapshot():
   rows,_=get_contest_ranking_list(request,self.contest,show_current_virtual=False)
   return ([(rank,row.participation.pk,row.participation.score,row.participation.cumtime) for rank,row in rows],
    Contest.objects.get(pk=self.contest.pk).user_count,list(ContestParticipation.objects.filter(contest=self.contest).values()),
    list(ContestSubmission.objects.filter(problem=self.cp).values()),list(type(self.v.problem).objects.filter(pk=self.v.problem.pk).values('ac_rate','user_count')))
  before=snapshot()
  for verdict in ('AC','WA'):
   with patch('cpjudge.author_tests.dispatch'):s,_=self.admit_test()
   Submission.objects.filter(pk=s.pk).update(status='D',result=verdict,case_points=3 if verdict=='AC' else 0,case_total=3)
   s.refresh_from_db();s.update_contest();s.problem.update_stats()
   self.assertEqual(snapshot(),before)
  self.assertEqual(AuthorTest.objects.count(),2)
 def test_source_runtime_version_and_ranked_row_tampering_rejected(self):
  with patch('cpjudge.author_tests.dispatch'):s,_=self.admit_test()
  from cpjudge.admission import validate_execution
  self.assertTrue(validate_execution(s))
  s.source.source='changed';s.source.save()
  with self.assertRaises(PermissionDenied):validate_execution(s)
  s.source.source='int main(){}';s.source.save()
  s.is_archived=False;s.save()
  with self.assertRaises(PermissionDenied):validate_execution(s)
  s.is_archived=True;s.contest_object=self.contest;s.save()
  with self.assertRaises(PermissionDenied):validate_execution(s)
 def test_conflict_direct_routes_and_prior_knowledge_across_contests(self):
  # Native navigation and a crafted official/test flag cannot admit the owner.
  c=self.logged('C5A');p=ContestParticipation.objects.create(user=self.owner.profile,contest=self.contest,virtual=0)
  profile=self.owner.profile;profile.current_contest=p;profile.save(update_fields=['current_contest'])
  data={'language':self.lang.pk,'source':'int main(){}','request_key':str(uuid.uuid4()),'test':'false','virtual':'0'}
  with patch('cpjudge.entries.server_now',return_value=self.running):
   for path in (f'/problem/{self.v.code}/submit',self.base+f'/problem/{self.v.code}/submit',self.base+'/join'):
    self.assertIn(c.post(path,data).status_code,(403,404))
   with self.assertRaises(PermissionDenied):self.submit(self.owner)
  # A selected version's importer stays conflicted even without a current grant.
  Conflict.objects.filter(user=self.owner,contest=self.contest).delete();Grant.objects.filter(user=self.owner,contest=self.contest).delete()
  self.assertTrue(e.conflict(self.owner,self.contest))
  self.assertFalse(e.conflict(self.p,self.contest))
 def test_stale_session_csrf_pending_language_and_approval(self):
  c=Client(enforce_csrf_checks=True);c.force_login(self.owner,backend='cpjudge.identity.CollegeBackend')
  self.assertEqual(c.post(self.path,{'source':'int main(){}'}).status_code,403)
  i=Identity.objects.get(user=self.owner)
  with self.assertRaises(PermissionDenied):t.admit(self.owner,self.contest.key,self.v.code,self.lang.pk,'int main(){}',str(uuid.uuid4()),generation=i.generation+1,auth_hash=self.owner.get_session_auth_hash())
  with self.assertRaises(PermissionDenied):self.admit_test(language=987654)
  a=ContestVersionAdmission.objects.get(contest_problem=self.cp);a.revoked=True;a.save()
  with self.assertRaises(Http404):self.admit_test()
  a.revoked=False;a.save()
  with patch('cpjudge.author_tests.dispatch'):self.admit_test()
  with self.assertRaises(PermissionDenied):self.admit_test()

for _name in dir(EntryTests):
 if _name.startswith('test_'):setattr(AuthorTests,_name,None)
