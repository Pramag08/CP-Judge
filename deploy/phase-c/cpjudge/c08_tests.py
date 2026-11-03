"""C08 stored-output, authorization, escaping and attempt isolation checks."""
import json
from unittest.mock import patch
import yaml
from django.test import TestCase
from cpjudge.integration_tests import NativeUploadHTTPTests
from cpjudge.imports import upload
from cpjudge.models import ImportJob,Grant
from cpjudge.conversion import attempt_path,queue_conversion
from cpjudge.compatibility import preview,rejection_message,CORRECTIONS,PUBLIC_REJECTIONS

class CompatibilityTests(TestCase):
 setUp=NativeUploadHTTPTests.setUp
 upload_file=NativeUploadHTTPTests.upload_file
 zip_bytes=NativeUploadHTTPTests.zip_bytes
 logged=NativeUploadHTTPTests.logged
 def stored(self):
  job=upload(self.users['C5A'],self.upload_file(),self.contests['c5a'])
  job.status='succeeded';job.attempt=1;job.token='a'*64
  job.findings={'slug':'fixture','converted_directory':'attempts/'+job.token+'/output'};job.save()
  self.base=attempt_path(job.token);output=self.base/'output';(output/'fixture').mkdir(parents=True)
  (self.base/'owner.json').write_text(json.dumps({'job_id':job.pk,'attempt':1,'token':job.token}))
  self.report={'source_sha256':job.package_sha256,'time_ms':1250,'memory_bytes':67108865,
    'checker_executor':'CPP23','checker_source_type':'x-g++23','test_hashes':[{},{}],'samples':[1],'issues':[]}
  self.config={'time_limit':1.25,'memory_limit':65537,'checker':{'args':{'lang':'CPP23'}},'test_cases':[{'points':1},{'points':1}]}
  self.meta={'code':'fixture','title':'<img src=x onerror="window.injected=1">'}
  self.output=output;self.write();return job
 def write(self):
  (self.output/'conversion-report.json').write_text(json.dumps(self.report))
  (self.output/'fixture.metadata.json').write_text(json.dumps(self.meta))
  (self.output/'fixture/init.yml').write_text(yaml.safe_dump(self.config))
 def test_output_counts_units_standard_and_escaped_name_after_refresh(self):
  job=self.stored();c=self.logged('C5A')
  for _ in range(2):
   r=c.get(f'/imports/{job.pk}/');self.assertContains(r,'Converted successfully')
   for text in ('1250 ms → 1.25 seconds','67108865 bytes → 65537 KiB','CPP23','Judging verified: No','Not ready for publication','&lt;img'):
    self.assertContains(r,text)
   self.assertNotContains(r,'<img src=x');self.assertNotContains(r,job.token)
   self.assertEqual(r['Cache-Control'],'private, no-store')
  self.assertEqual(preview(job)['test_count'],2);self.assertEqual(preview(job)['sample_count'],1)
 def test_groups_and_dependencies_come_from_native_output(self):
  job=self.stored();self.config['test_cases']=[{'batched':[{}],'points':30},{'batched':[{}],'points':70,'dependencies':[1]}];self.write()
  self.assertEqual(preview(job)['groups'],[{'number':1,'tests':1,'points':30,'dependencies':[]},{'number':2,'tests':1,'points':70,'dependencies':[1]}])
  self.assertContains(self.logged('C5A').get(f'/imports/{job.pk}/'),'Complete-group scoring')
 def test_nonterminal_and_failed_states_ignore_stale_findings(self):
  job=self.stored();c=self.logged('C5A')
  for state in ('uploaded','queued','running','failed'):
   ImportJob.objects.filter(pk=job.pk).update(status=state,error='<script>window.injected=1</script>')
   r=c.get(f'/imports/{job.pk}/');self.assertNotContains(r,'id="compatibility-preview"')
   self.assertNotContains(r,'1250 ms');self.assertNotContains(r,'<script>window.injected=1</script>')
  job.refresh_from_db()
  with patch('cpjudge.conversion.publish_attempt'),self.captureOnCommitCallbacks(execute=True):queue_conversion(job.owner,job.pk)
  job.refresh_from_db();self.assertEqual(job.findings,{});self.assertEqual(job.attempt,2)
 def test_wrong_attempt_receipt_hash_or_units_fail_closed(self):
  job=self.stored();self.report['source_sha256']='other';self.write();self.assertIsNone(preview(job))
  self.report['source_sha256']=job.package_sha256;self.config['memory_limit']=65536;self.write();self.assertIsNone(preview(job))
  self.config['memory_limit']=65537;self.config['test_cases']=[];self.write();self.assertIsNone(preview(job))
  self.config['test_cases']=[{},{}];self.write();job.attempt=2;self.assertIsNone(preview(job))
  job.attempt=1;job.findings['converted_directory']='other-attempt';self.assertIsNone(preview(job))
 def test_participant_unrelated_author_and_revoked_owner_denied(self):
  job=self.stored()
  for role in ('C5P','C5B'):
   self.assertIn(self.logged(role).get(f'/imports/{job.pk}/').status_code,(403,404))
  c=self.logged('C5A');Grant.objects.filter(user=job.owner,capability='problems.import').update(revoked=True)
  self.assertEqual(c.get(f'/imports/{job.pk}/').status_code,403)
 def test_rejection_guidance_is_fixed_actionable_and_does_not_echo_private_text(self):
  for reason,correction in CORRECTIONS.items():
   self.assertEqual(rejection_message(ValueError(reason)),correction)
   self.assertIn(correction,PUBLIC_REJECTIONS)
  for reason in ('missing required package file: /private/secret','unsafe package path: <script>alert(1)</script>','/tmp/raw-secret'):
   text=rejection_message(ValueError(reason));self.assertNotIn('secret',text);self.assertNotIn('<script>',text)
  self.assertIn('genuinely non-interactive',rejection_message(ValueError('interactive problems unsupported')))
 def test_missing_persisted_metadata_is_not_inferred(self):
  job=self.stored();(self.output/'fixture.metadata.json').unlink()
  r=self.logged('C5A').get(f'/imports/{job.pk}/');self.assertContains(r,'Verified compatibility details are unavailable')
  self.assertNotContains(r,'id="compatibility-preview"')
