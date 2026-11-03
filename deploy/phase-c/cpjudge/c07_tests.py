"""Focused C07 request, commit, delivery and reconciliation checks."""
import datetime
from unittest.mock import patch
from django.test import TestCase, Client
from django.utils import timezone
from cpjudge.integration_tests import NativeUploadHTTPTests
from cpjudge.models import ImportJob,Grant
from cpjudge.imports import upload
from cpjudge import conversion

class ConversionTests(TestCase):
 setUp=NativeUploadHTTPTests.setUp
 upload_file=NativeUploadHTTPTests.upload_file
 zip_bytes=NativeUploadHTTPTests.zip_bytes
 logged=NativeUploadHTTPTests.logged
 def stored(self):
  return upload(self.users['C5A'],self.upload_file(),self.contests['c5a'])
 def queued(self):
  job=self.stored()
  with patch.object(conversion,'publish_attempt'),self.captureOnCommitCallbacks(execute=True):
   conversion.queue_conversion(self.users['C5A'],job.pk)
  job.refresh_from_db();return job

 def test_commit_only_queue_and_duplicate_request(self):
  job=self.stored()
  with patch.object(conversion,'publish_attempt') as publish:
   with self.captureOnCommitCallbacks(execute=True) as callbacks:
    conversion.queue_conversion(self.users['C5A'],job.pk)
    conversion.queue_conversion(self.users['C5A'],job.pk)
    publish.assert_not_called()
   self.assertEqual(len(callbacks),1);publish.assert_called_once()
  job.refresh_from_db();self.assertEqual(job.status,'queued');self.assertEqual(job.attempt,1)
  self.assertTrue(job.token)

 def test_broker_failure_is_terminal_and_retry_uses_new_token(self):
  from cpjudge.tasks import convert_upload
  job=self.stored()
  with patch.object(convert_upload,'apply_async',side_effect=OSError('private broker details')),self.captureOnCommitCallbacks(execute=True):
   conversion.queue_conversion(self.users['C5A'],job.pk)
  job.refresh_from_db();self.assertEqual(job.status,'failed');self.assertNotIn('private broker details',job.error)
  old=job.token
  with patch.object(conversion,'publish_attempt'),self.captureOnCommitCallbacks(execute=True):conversion.queue_conversion(self.users['C5A'],job.pk)
  job.refresh_from_db();self.assertEqual(job.attempt,2);self.assertNotEqual(job.token,old)

 def test_duplicate_delivery_claims_once_and_refresh_is_persistent(self):
  job=self.queued()
  with patch.object(conversion,'run_conversion',return_value={'conversion':'test-only receipt'}) as runner:
   conversion.execute_conversion(job.pk,job.attempt,job.token)
   conversion.execute_conversion(job.pk,job.attempt,job.token)
   runner.assert_called_once()
  job.refresh_from_db();self.assertEqual(job.status,'succeeded');self.assertEqual(job.attempt,1)
  client=self.logged('C5A');url=f'/imports/{job.pk}/'
  self.assertContains(client.get(url),'succeeded');self.assertContains(client.get(url),'succeeded')

 def test_revoked_owner_is_rechecked_at_execution(self):
  job=self.queued();Grant.objects.filter(user=self.users['C5A'],capability='problems.import').update(revoked=True)
  with patch.object(conversion,'run_conversion') as runner:conversion.execute_conversion(job.pk,job.attempt,job.token);runner.assert_not_called()
  job.refresh_from_db();self.assertEqual(job.status,'failed')

 def test_stale_queued_and_running_attempts_reconcile_without_old_overwrite(self):
  job=self.queued();old=(job.attempt,job.token)
  self.assertGreaterEqual(conversion.reconcile_imports(now=timezone.now()+datetime.timedelta(seconds=1000)),1)
  job.refresh_from_db();self.assertEqual(job.status,'failed')
  with patch.object(conversion,'publish_attempt'),self.captureOnCommitCallbacks(execute=True):conversion.queue_conversion(self.users['C5A'],job.pk)
  job.refresh_from_db();new=(job.attempt,job.token)
  with patch.object(conversion,'run_conversion') as runner:conversion.execute_conversion(job.pk,*old);runner.assert_not_called()
  job.refresh_from_db();self.assertEqual((job.status,job.attempt,job.token),('queued',*new))
  ImportJob.objects.filter(pk=job.pk).update(status='running',started_at=timezone.now()-datetime.timedelta(seconds=1000))
  self.assertGreaterEqual(conversion.reconcile_imports(),1)
  job.refresh_from_db();self.assertEqual(job.status,'failed')

 def test_stale_running_completion_cannot_overwrite_new_attempt(self):
  job=self.queued();old_attempt=job.attempt;old_token=job.token
  def superseded(*args):
   ImportJob.objects.filter(pk=job.pk).update(attempt=old_attempt+1,token='newer-token',status='queued',findings={})
   return {'stale':'must never be published'}
  with patch.object(conversion,'run_conversion',side_effect=superseded):conversion.execute_conversion(job.pk,old_attempt,old_token)
  job.refresh_from_db();self.assertEqual(job.status,'queued');self.assertEqual(job.findings,{})

 def test_error_details_are_private_and_action_is_csrf_protected(self):
  for detail in ('/private/internal/secret','Package validation failed. /private/path'):
   job=self.queued()
   with patch.object(conversion,'run_conversion',side_effect=OSError(detail)):conversion.execute_conversion(job.pk,job.attempt,job.token)
   job.refresh_from_db();self.assertEqual(job.status,'failed');self.assertNotIn('/private/',job.error)
  other=self.logged('C5B');self.assertEqual(other.get(f'/imports/{job.pk}/').status_code,404)
  self.assertEqual(other.post(f'/imports/{job.pk}/convert/').status_code,404)
  csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.users['C5A'])
  self.assertEqual(csrf.get(f'/imports/{job.pk}/').status_code,200)
  self.assertEqual(csrf.post(f'/imports/{job.pk}/convert/').status_code,403)

 def test_rolled_back_queue_admission_never_publishes(self):
  from django.db import transaction
  job=self.stored()
  with patch.object(conversion,'publish_attempt') as publish,self.captureOnCommitCallbacks(execute=True) as callbacks:
   with self.assertRaises(RuntimeError):
    with transaction.atomic():
     conversion.queue_conversion(self.users['C5A'],job.pk)
     raise RuntimeError('Rollback admission')
   self.assertEqual(callbacks,[])
   publish.assert_not_called()
  job.refresh_from_db();self.assertEqual((job.status,job.attempt),('uploaded',0))

 def test_existing_attempt_directory_and_mismatched_owner_are_preserved(self):
  import json
  job=self.queued();root=conversion.attempt_path(job.token);root.mkdir(parents=True)
  sentinel=root/'keep';sentinel.write_text('existing output')
  with patch('cpjudge.conversion.subprocess.Popen') as spawn,self.assertRaises(FileExistsError):
   conversion.run_conversion(job,job.attempt,job.token)
  spawn.assert_not_called();self.assertEqual(sentinel.read_text(),'existing output')
  (root/'owner.json').write_text(json.dumps({'job_id':job.pk+1,'attempt':job.attempt,'token':job.token}))
  conversion.cleanup_attempt(job.pk,job.attempt,job.token)
  self.assertEqual(sentinel.read_text(),'existing output')
  (root/'owner.json').write_text(json.dumps({'job_id':job.pk,'attempt':job.attempt,'token':job.token}))
  conversion.cleanup_attempt(job.pk,job.attempt,job.token)
  self.assertFalse(root.exists())

 def test_legacy_synchronous_helper_cannot_touch_tokenized_attempt(self):
  from django.core.exceptions import ValidationError
  from cpjudge.imports import convert_job
  job=self.queued();before=list(ImportJob.objects.filter(pk=job.pk).values())[0]
  with patch('compat.convert.convert') as writer,self.assertRaises(ValidationError):convert_job(job.pk)
  writer.assert_not_called()
  self.assertEqual(list(ImportJob.objects.filter(pk=job.pk).values())[0],before)

from django.test import TransactionTestCase
class ConversionRaceTests(TransactionTestCase):
 setUp=NativeUploadHTTPTests.setUp
 upload_file=NativeUploadHTTPTests.upload_file
 zip_bytes=NativeUploadHTTPTests.zip_bytes
 def test_concurrent_queue_requests_admit_only_one_attempt(self):
  from concurrent.futures import ThreadPoolExecutor
  from django.db import close_old_connections
  from django.contrib.auth import get_user_model
  import threading
  job=upload(self.users['C5A'],self.upload_file(),self.contests['c5a']);uid=self.users['C5A'].pk
  barrier=threading.Barrier(2)
  def queue(_):
   close_old_connections()
   try:
    user=get_user_model().objects.get(pk=uid);barrier.wait(timeout=10)
    value=conversion.queue_conversion(user,job.pk)
    return value.attempt,value.token
   finally:close_old_connections()
  with patch.object(conversion,'publish_attempt') as publish:
   with ThreadPoolExecutor(2) as pool:values=list(pool.map(queue,range(2)))
   self.assertEqual(values[0],values[1]);self.assertEqual(values[0][0],1);publish.assert_called_once()
  job.refresh_from_db();self.assertEqual(job.status,'queued')
