"""Focused probe admission/binding/privacy; actual execution is browser evidence."""
from unittest.mock import patch
from django.test import Client
from cpjudge.c10_tests import PublicationTests
from cpjudge import probes
from cpjudge.models import ProbeSolution,ProblemProbe
from judge.models import Language,ContestSubmission

class ProbeTests(PublicationTests):
 # Inherit fixture helpers only; don't repeat C10 acceptance.
 def setUp(self):
  super().setUp()
  from cpjudge.publication import publish
  self.v=publish(self.users['C5A'],self.job().pk,1)
  self.lang,_=Language.objects.get_or_create(key='CPP17',defaults={'name':'C++17','short_name':'C++','common_name':'C++','extension':'cpp','ace':'c_cpp','pygments':'cpp'})
  self.sol=ProbeSolution.objects.create(version=self.v,owner=self.users['C5A'],name='known',runtime=self.lang,source='int main(){}',sha256=probes.fingerprint('int main(){}'))
  self.url=f'/private-versions/{self.v.pk}/probes/'
 def test_probe_binding_privacy_quota_and_stale(self):
  c=self.logged('C5A');payload={'digest':self.v.digest,'solution':self.sol.pk,'solution_digest':self.sol.sha256}
  for client in (Client(),self.logged('C5B'),self.logged('C5P')):
   self.assertIn(client.post(self.url+'run/',payload).status_code,(401,403,404))
  self.assertEqual(c.post(self.url+'run/',dict(payload,digest='0'*64)).status_code,409)
  self.assertEqual(c.get(self.url+'run/').status_code,405)
  with patch('cpjudge.probes.dispatch') as dispatch:
   self.assertEqual(c.post(self.url+'run/',payload).status_code,302);dispatch.assert_called_once()
  probe=ProblemProbe.objects.get();self.assertTrue(probes.binding(probe));s=probe.execution
  self.assertFalse(ContestSubmission.objects.filter(submission=s).exists());self.assertIsNone(s.contest_object_id)
  self.assertEqual(c.post(self.url+'run/',payload).status_code,429)
  from cpjudge.native import review,visible_submissions
  from judge.models import Submission
  self.assertFalse(review(self.users['C5A'],s));self.assertFalse(visible_submissions(self.users['C5A'],Submission.objects.all()).filter(pk=s.pk).exists())
  for url in (f'/submission/{s.pk}',f'/src/{s.pk}/raw',f'/widgets/submission_testcases?id={s.pk}',f'/cpjudge/events/sub_{s.id_secret}'):
   self.assertEqual(c.get(url).status_code,404)
  ProbeSolution.objects.filter(pk=self.sol.pk).update(source='changed')
  probe.solution.refresh_from_db()
  with self.assertRaises(ValueError):probes.binding(probe)
  self.assertContains(c.get(self.url),'Stale inputs')
 def test_expiry_csrf_and_runtime_readiness(self):
  from django.utils import timezone
  from datetime import timedelta
  c=self.logged('C5A');payload={'digest':self.v.digest,'solution':self.sol.pk,'solution_digest':self.sol.sha256}
  with patch('cpjudge.probes.dispatch'):c.post(self.url+'run/',payload)
  probe=ProblemProbe.objects.get();probe.expires=timezone.now()-timedelta(seconds=1);probe.save()
  with self.assertRaises(ValueError):probes.binding(probe,dispatch=True)
  with patch('judge.models.Submission.abort') as abort:probes.expire(probe.pk);abort.assert_called_once()
  client=Client(enforce_csrf_checks=True);client.force_login(self.users['C5A'],backend='cpjudge.identity.CollegeBackend')
  self.assertEqual(client.post(self.url+'run/',payload).status_code,403)
  self.assertFalse(self.v.problem.allowed_languages.exists());self.assertFalse(self.v.problem.is_public)

# Remove inherited tests: C10 evidence is already accepted.
for _name in dir(PublicationTests):
 if _name.startswith('test_'):setattr(ProbeTests,_name,None)
