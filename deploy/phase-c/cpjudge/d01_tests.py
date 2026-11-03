"""Focused real DB/HTTP tests; worker challenge mocked only in positive fixtures."""
from datetime import timedelta
from unittest.mock import patch
from django.test import Client
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from cpjudge.integrated_tests import AdmissionTests
from cpjudge.models import ContestWorkflow, ContestProblemLabel, ContestVersionAdmission, Grant
from cpjudge.contest_manage import FIXED,DraftForm,readiness,state
from cpjudge.native import contest_access,problem_access
from cpjudge.admission import participant_approval,frozen_rules,validate_execution
from judge.models import Contest,ContestProblem,Submission,SubmissionSource,ContestSubmission

class WorkflowTests(AdmissionTests):
 def setUp(self):
  super().setUp()
  for key,value in FIXED.items():setattr(self.contest,key,value)
  self.contest.is_visible=False;self.contest.save()
  ContestWorkflow.objects.create(contest=self.contest,owner=self.users['C5A'])
  ContestProblemLabel.objects.create(contest_problem=self.cp,label='Q')
  Grant.objects.get_or_create(user=self.users['C5A'],contest=self.contest,capability='settings.edit',defaults={'grantor':self.admin})
  from cpjudge.models import Identity
  Identity.objects.filter(user=self.users['C5P']).update(canonical_email='c5p@private.invalid')
  self.url=f'/author/contests/{self.contest.key}/'
  self.payload={'name':'Updated supervised contest','description':'Plain text','display_timezone':'Asia/Kolkata',
   'start_time':(timezone.now()+timedelta(days=2)).strftime('%Y-%m-%d 10:00'),
   'end_time':(timezone.now()+timedelta(days=2)).strftime('%Y-%m-%d 12:00')}
 def select(self,**extra):
  return self.logged('C5A').post(self.url+'problem/',dict(version=self.v.pk,label='Q',order=2,**extra))
 def test_d01_create_edit_scope_and_crafted_formats(self):
  data=dict(self.payload,key='d01new')
  for who in ('C5P',):self.assertEqual(self.logged(who).post('/author/contests/create/',data).status_code,403)
  a=self.logged('C5A');self.assertEqual(a.post('/author/contests/create/',dict(data,format_name='ioi')).status_code,400)
  self.assertEqual(a.post('/author/contests/create/',data).status_code,302)
  c=Contest.objects.get(key='d01new');self.assertFalse(c.is_visible);self.assertEqual(c.format_name,'cpjudge_icpc_v1')
  self.assertEqual(a.post(self.url,self.payload).status_code,302)
  self.contest.refresh_from_db();self.assertEqual(self.contest.start_time.hour,4);self.assertEqual(self.contest.start_time.minute,30)
  for who in ('C5P','C5B'):
   client=self.logged(who)
   for suffix in ('','preview/','publish/','problem/','remove/'):
    self.assertIn(client.post(self.url+suffix,self.payload).status_code,(403,404,405))
   self.assertIn(client.get(self.url).status_code,(403,404))
  for suffix in ('','preview/'):
   self.assertEqual(a.get(self.url+suffix).status_code,200)
 def test_d02_select_order_labels_limits_and_unauthorized_version(self):
  self.assertEqual(self.select().status_code,302)
  self.cp.refresh_from_db();self.assertEqual(self.cp.order,2);self.assertEqual(self.cp.workflow_label.label,'Q')
  self.assertEqual((self.cp.problem.time_limit,self.cp.problem.memory_limit),(0.5,65536))
  self.assertEqual(self.contest.get_label_for_problem(0),'Q')
  self.assertFalse(self.v.problem.is_public)
  self.assertEqual(self.logged('C5A').post(self.url+'problem/',{'version':99999,'label':'A','order':0}).status_code,400)
 def test_d03_invalid_timezone_schedule_dst_and_unknown_controls(self):
  for changes in ({'end_time':self.payload['start_time']},{'display_timezone':'bad/zone'},
   {'start_time':'2020-01-01 00:00'}, {'display_timezone':'America/New_York','start_time':'2027-11-07 01:30'},
   {'display_timezone':'America/New_York','start_time':'2027-03-14 02:30'}, {'time_limit':'10'}, {'is_rated':'on'}):
   self.assertFalse(DraftForm(dict(self.payload,key='validkey',**{})|changes).is_valid())
 def test_d04_draft_future_direct_api_asset_and_no_registration(self):
  p=self.users['C5P'];a=self.logged('C5A');participant=self.logged('C5P')
  self.assertFalse(contest_access(p,self.contest));self.assertFalse(problem_access(p,self.v.problem))
  for path in (f'/contest/{self.contest.key}',f'/problem/{self.v.code}',f'/problem/{self.v.code}/published-assets/statement.css',f'/api/v2/problem/{self.v.code}'):
   self.assertIn(participant.get(path).status_code,(403,404))
  self.release();self.contest.is_visible=True;self.contest.save(update_fields=['is_visible'])
  ContestVersionAdmission.objects.update(rules=frozen_rules(self.contest))
  self.assertTrue(contest_access(p,self.contest))
  self.assertEqual(participant.get(f'/contest/{self.contest.key}').status_code,200)
  self.assertFalse(problem_access(p,self.v.problem))
  self.assertEqual(participant.post(f'/contest/{self.contest.key}/join').status_code,302)
  self.assertFalse(problem_access(p,self.v.problem))
  for path in ('/problems/','/problem/'+self.v.code+'/editorial'):
   self.assertIn(participant.get(path).status_code,(403,404))
 def test_d05_fixed_settings_immutable_after_publication(self):
  self.select()
  with patch('cpjudge.contest_readiness.check'):
   self.assertEqual(self.logged('C5A').post(self.url+'publish/').status_code,302)
  self.contest.refresh_from_db();self.assertTrue(self.contest.is_visible)
  from cpjudge.publication import verify_native
  self.assertTrue(verify_native(self.v))
  for suffix,data in (('',self.payload),('problem/',{'version':self.v.pk,'label':'B','order':0}),('remove/',{'problem':self.cp.pk})):
   self.assertEqual(self.logged('C5A').post(self.url+suffix,data).status_code,403)
  self.assertTrue(ContestVersionAdmission.objects.filter(contest_problem=self.cp,revoked=False).exists())
 def test_d06_missing_stale_probe_worker_rules_block_then_publish(self):
  a=self.logged('C5A')
  self.assertIn('no accepted private probe is bound',readiness(self.contest)[0])
  self.assertEqual(a.post(self.url+'publish/').status_code,409)
  self.select();a=self.logged('C5A')
  with patch('cpjudge.contest_readiness.check',side_effect=ValueError('offline')):
   self.assertIn('compatible live worker has not verified',readiness(self.contest)[0])
   self.assertEqual(a.post(self.url+'publish/').status_code,409)
  with patch('cpjudge.contest_readiness.check'):
   self.assertFalse(readiness(self.contest))
   Submission.objects.filter(pk=self.probe.execution_id).update(result='WA')
   self.assertIn('accepted private probe or contest approval is stale',readiness(self.contest)[0])
   self.assertEqual(a.post(self.url+'publish/').status_code,409)
   Submission.objects.filter(pk=self.probe.execution_id).update(result='AC')
   self.assertEqual(a.post(self.url,self.payload).status_code,302)
   self.assertEqual(a.post(self.url+'publish/').status_code,409)
   self.assertEqual(self.select().status_code,302)
   self.assertFalse(readiness(Contest.objects.get(pk=self.contest.pk)))
   client=self.logged('C5A')
   self.assertEqual(client.post(self.url+'remove/',{'problem':self.cp.pk}).status_code,302)
   self.v.problem.refresh_from_db();self.assertFalse(self.v.problem.allowed_languages.exists())
   self.assertEqual(self.select().status_code,302)
 def test_server_start_end_inclusive_exclusive_and_receipt(self):
  self.release();self.entry();self.contest.is_visible=True;self.contest.save(update_fields=['is_visible'])
  ContestVersionAdmission.objects.update(rules=frozen_rules(self.contest))
  u=self.users['C5P']
  from cpjudge.entries import register
  register(u,self.contest.key)
  for now,expected in ((self.contest.start_time-timedelta(microseconds=1),False),(self.contest.start_time,True),
      (self.contest.end_time-timedelta(microseconds=1),True),(self.contest.end_time,False)):
   with patch('cpjudge.admission.timezone.now',return_value=now):self.assertEqual(bool(participant_approval(u,self.v.problem,submit=True)),expected)
  self.assertEqual(state(self.contest,self.contest.start_time)[0],'Running')
  self.assertEqual(state(self.contest,self.contest.end_time),('Ended',0))
  from cpjudge.entries import admit
  from cpjudge.models import Identity
  import uuid
  with patch('cpjudge.entries.server_now',return_value=self.contest.start_time),patch('cpjudge.entries.dispatch'):
   s,_=admit(u,self.contest.key,self.v.code,self.lang.pk,'receipt fixture',str(uuid.uuid4()),generation=Identity.objects.get(user=u).generation,auth_hash=u.get_session_auth_hash())
  for when,valid in ((self.contest.start_time,True),(self.contest.end_time,False)):
   Submission.objects.filter(pk=s.pk).update(date=when);s.refresh_from_db()
   if valid:self.assertTrue(validate_execution(s))
   else:
    with self.assertRaises(PermissionDenied):validate_execution(s)
 def test_csrf_and_methods(self):
  home=self.logged('C5A').get('/')
  self.assertEqual(home.status_code,302);self.assertEqual(home['Location'],'/contests/')
  self.assertEqual(self.logged('C5A').get(self.url+'publish/').status_code,405)
  c=Client(enforce_csrf_checks=True);c.force_login(self.users['C5A'],backend='cpjudge.identity.CollegeBackend')
  self.assertEqual(c.post(self.url+'publish/').status_code,403)

for _name in dir(AdmissionTests):
 if _name.startswith('test_'):setattr(WorkflowTests,_name,None)
