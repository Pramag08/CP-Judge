"""Constructed DB approval negatives; actual judging is a separate browser proof."""
from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone
from django.http import Http404
from django.core.exceptions import PermissionDenied
from judge.models import Contest,ContestProblem,ContestParticipation,Submission,SubmissionSource,SubmissionTestCase,Judge,Language
from cpjudge.c13_tests import ProbeTests
from cpjudge.models import Grant,ProblemProbe,ContestVersionAdmission,Conflict
from cpjudge.publication import verify_native,PublicationError
from cpjudge.admission import approve,participant_approval,validate_execution,native_languages

class AdmissionTests(ProbeTests):
 def setUp(self):
  super().setUp();now=timezone.now()
  self.contest=Contest.objects.create(key='integratedcheck',name='Private integrated fixture',description='Fixture',start_time=now+timedelta(minutes=5),end_time=now+timedelta(hours=1),is_visible=True,is_private=True,is_rated=False,time_limit=None,format_name='cpjudge_icpc_v1',format_config={'penalty':20})
  self.cp=ContestProblem.objects.create(contest=self.contest,problem=self.v.problem,order=0,points=1,partial=False)
  Grant.objects.create(user=self.users['C5A'],contest=self.contest,capability='problems.publish',grantor=self.admin)
  self.contest.private_contestants.add(self.users['C5P'].profile)
  self.worker=Judge.objects.create(name='integrated-test-worker',auth_key='synthetic-auth-not-live',online=True)
  self.worker.problems.add(self.v.problem);self.worker.runtimes.add(self.lang)
  s=Submission.objects.create(user=self.users['C5A'].profile,problem=self.v.problem,language=self.lang,status='D',result='AC',case_points=3,case_total=3)
  SubmissionSource.objects.create(submission=s,source=self.sol.source)
  for i in range(1,4):SubmissionTestCase.objects.create(submission=s,case=i,status='AC',time=.01,memory=1000,points=1,total=1)
  self.probe=ProblemProbe.objects.create(version=self.v,solution=self.sol,owner=self.users['C5A'],execution=s,problem_digest=self.v.digest,solution_digest=self.sol.sha256,runtime_key=self.lang.key,expires=now+timedelta(seconds=120))
 def release(self):return approve(self.users['C5A'],self.v,self.contest,self.probe)
 def entry(self):
  e=ContestParticipation.objects.create(contest=self.contest,user=self.users['C5P'].profile,virtual=0)
  p=self.users['C5P'].profile;p.current_contest=e;p.save(update_fields=['current_contest'])
  return e
 def test_approval_requires_scoped_owner_complete_probe_and_online_worker(self):
  with self.assertRaises((PermissionDenied,Http404)):approve(self.users['C5B'],self.v,self.contest,self.probe)
  Submission.objects.filter(pk=self.probe.execution_id).update(result='WA')
  with self.assertRaises(ValueError):self.release()
  self.assertFalse(ContestVersionAdmission.objects.exists());self.assertFalse(self.v.problem.allowed_languages.exists())
  Submission.objects.filter(pk=self.probe.execution_id).update(result='AC')
  Judge.objects.filter(pk=self.worker.pk).update(online=False)
  with self.assertRaises(PermissionDenied):self.release()
  Judge.objects.filter(pk=self.worker.pk).update(online=True)
  a=self.release();self.assertTrue(verify_native(self.v));self.assertEqual(native_languages(self.v),['CPP17'])
  self.assertFalse(self.v.problem.is_public);self.assertEqual(self.v.manifest['allowed_languages'],[])
 def test_only_registered_allowlisted_official_entry_can_submit_in_window(self):
  self.release();u=self.users['C5P'];self.assertIsNone(participant_approval(u,self.v.problem,submit=True))
  e=self.entry();live=self.contest.start_time+timedelta(seconds=1)
  with patch('cpjudge.admission.timezone.now',return_value=live):
   self.assertIsNotNone(participant_approval(u,self.v.problem,submit=True))
   self.assertIsNone(participant_approval(self.users['C5B'],self.v.problem,submit=True))
   self.assertIsNone(participant_approval(self.admin,self.v.problem,submit=True))
   self.contest.banned_users.add(u.profile);self.assertIsNone(participant_approval(u,self.v.problem,submit=True));self.contest.banned_users.clear()
   Conflict.objects.create(user=u,contest=self.contest);self.assertIsNone(participant_approval(u,self.v.problem,submit=True))
   Conflict.objects.filter(user=u,contest=self.contest).delete()
   ContestParticipation.objects.filter(pk=e.pk).update(virtual=1);self.assertIsNone(participant_approval(u,self.v.problem,submit=True))
  with patch('cpjudge.admission.timezone.now',return_value=self.contest.end_time):self.assertIsNone(participant_approval(u,self.v.problem,submit=True))
 def test_changed_version_source_runtime_rules_and_incomplete_cases_invalidate(self):
  self.release();self.assertTrue(verify_native(self.v))
  self.sol.source='changed';self.sol.save(update_fields=['source'])
  with self.assertRaises(ValueError):verify_native(self.v)
  self.sol.source='int main(){}';self.sol.save(update_fields=['source'])
  Contest.objects.filter(pk=self.contest.pk).update(format_config={'penalty':10})
  with self.assertRaises(ValueError):verify_native(self.v)
  Contest.objects.filter(pk=self.contest.pk).update(format_config={'penalty':20})
  SubmissionTestCase.objects.filter(submission=self.probe.execution,case=3).delete()
  with self.assertRaises(ValueError):verify_native(self.v)
 def test_final_execution_requires_exact_native_contest_runtime_and_entry(self):
  self.release();entry=self.entry();u=self.users['C5P']
  s=Submission.objects.create(user=u.profile,problem=self.v.problem,language=self.lang,contest_object=self.contest)
  from judge.models import ContestSubmission
  ContestSubmission.objects.create(submission=s,problem=self.cp,participation=entry)
  SubmissionSource.objects.create(submission=s,source='ordinary participant source')
  Submission.objects.filter(pk=s.pk).update(date=self.contest.start_time+timedelta(seconds=2));s.refresh_from_db()
  self.assertEqual(validate_execution(s).version_id,self.v.pk)
  ContestParticipation.objects.filter(pk=entry.pk).update(virtual=1)
  with self.assertRaises(PermissionDenied):validate_execution(s)
  ContestParticipation.objects.filter(pk=entry.pk).update(virtual=0)
  Submission.objects.filter(pk=s.pk).update(date=self.contest.end_time);s.refresh_from_db()
  with self.assertRaises(PermissionDenied):validate_execution(s)

# Reuse fixture helpers; earlier C10/C13 suites have their own retained evidence.
for _name in dir(ProbeTests):
 if _name.startswith('test_'):setattr(AdmissionTests,_name,None)
