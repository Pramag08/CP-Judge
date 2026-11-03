"""C10 native DB/filesystem publication tests. No worker install or judging."""
import atexit,io,json,os,secrets,shutil,subprocess,sys,tempfile,threading,zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
import yaml
from django.test import TransactionTestCase,Client,override_settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import close_old_connections,connection,IntegrityError
from django.contrib.auth import get_user_model
from cpjudge import publication as pub
from cpjudge import integration_tests as native_tests
from cpjudge.models import ImportJob,ProblemVersion,Grant,Audit
from cpjudge.imports import upload,private_root
from cpjudge.conversion import attempt_path
from judge.models import Problem,ContestProblem,Submission

_TEMPLATES={}
def template(kind):
 if kind not in _TEMPLATES:
  from compat.convert import convert
  os.environ['PCC_ROOT']='/tmp/cpj-pcc'
  os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0='/tmp/cpj-pcc')
  folder=Path(tempfile.mkdtemp(prefix='c10-conversion-'));atexit.register(shutil.rmtree,folder,ignore_errors=True)
  package=Path('/tmp/c10-'+kind+'.zip');slug=convert(package,folder/'output')
  _TEMPLATES[kind]=(package,folder/'output',slug)
 return _TEMPLATES[kind]

class PublicationTests(TransactionTestCase):
 upload_file=native_tests.NativeUploadHTTPTests.upload_file
 zip_bytes=native_tests.NativeUploadHTTPTests.zip_bytes
 logged=native_tests.NativeUploadHTTPTests.logged
 def setUp(self):
  cache.clear();native_tests.NativeUploadHTTPTests.setUp(self)
  override=override_settings(CPJ_ARCHIVE_LIMITS={'upload_bytes':32*1024**2});override.enable();self.addCleanup(override.disable)
  self.addCleanup(self.writable)
  Grant.objects.create(user=self.users['C5A'],contest=self.contests['c5a'],capability='problems.publish',grantor=self.admin)
 def writable(self):
  for directory,_,_ in os.walk(self.temp.name):Path(directory).chmod(0o700)
 def job(self,kind='package',unique=False):
  package,out,slug=template(kind);data=package.read_bytes()
  if unique:
   stream=io.BytesIO(data)
   with zipfile.ZipFile(stream,'a') as z:z.comment=secrets.token_bytes(16)
   data=stream.getvalue()
  j=upload(self.users['C5A'],self.upload_file(data),self.contests['c5a'])
  j.status='succeeded';j.attempt=1;j.token=secrets.token_hex(32)
  j.findings={'slug':slug,'converted_directory':'attempts/'+j.token+'/output'};j.save()
  base=attempt_path(j.token);shutil.copytree(out,base/'output')
  (base/'owner.json').write_text(json.dumps({'job_id':j.pk,'attempt':j.attempt,'token':j.token}))
  report=base/'output/conversion-report.json';r=json.loads(report.read_text());r['source_sha256']=j.package_sha256;report.write_text(json.dumps(r))
  return j
 def test_success_native_limits_checker_cases_sanitized_files_and_private(self):
  j=self.job();v=pub.publish(j.owner,j.pk,1);self.assertTrue(pub.verify_native(v))
  p=v.problem;self.assertEqual((p.time_limit,p.memory_limit),(0.5,65536));self.assertFalse(p.is_public);self.assertTrue(p.is_manually_managed)
  self.assertFalse(p.allowed_languages.exists());self.assertFalse(ContestProblem.objects.filter(problem=p).exists())
  self.assertEqual(v.manifest['checker']['args']['lang'],'CPP17');self.assertEqual(len(v.manifest['test_cases']),3)
  self.assertFalse((pub.destination(v)/'attachments').exists());self.assertFalse((pub.destination(v)/'raw.zip').exists())
  self.assertEqual(ProblemVersion.objects.count(),1);self.assertEqual(Audit.objects.filter(action='problem.publish').count(),1)
  self.assertTrue(all(not (f.stat().st_mode&0o222) for f in pub.destination(v).rglob('*') if f.is_file()))
 def test_group_points_dependencies_and_order_are_preserved(self):
  j=self.job('groups');v=pub.publish(j.owner,j.pk,1)
  self.assertEqual(v.problem.points,100);self.assertEqual([c['points'] for c in v.manifest['test_cases']],[30,50,20])
  self.assertEqual(v.manifest['test_cases'][1]['dependencies'],[1]);self.assertTrue(pub.verify_native(v))
 def test_duplicate_requests_return_same_immutable_version_and_audit(self):
  j=self.job();first=pub.publish(j.owner,j.pk,1);path=pub.destination(first)/'data.zip';before=path.stat()
  second=pub.publish(j.owner,j.pk,1);after=path.stat()
  self.assertEqual(first.pk,second.pk);self.assertEqual((before.st_ino,before.st_mtime_ns),(after.st_ino,after.st_mtime_ns))
  self.assertEqual(ProblemVersion.objects.count(),1);self.assertEqual(Audit.objects.filter(action='problem.publish').count(),1)
 def test_authorization_csrf_get_and_stale_or_failed_attempts(self):
  j=self.job();url=f'/imports/{j.pk}/publish/'
  for c in (Client(),self.logged('C5B'),self.logged('C5P')):
   self.assertIn(c.post(url,{'attempt':1}).status_code,(401,403,404))
  c=self.logged('C5A');self.assertEqual(c.get(url).status_code,405)
  csrf=Client(enforce_csrf_checks=True);csrf.get('/accounts/login/')
  token=csrf.cookies['csrftoken'].value
  self.assertEqual(csrf.post('/accounts/login/',{'username':'C5A','password':self.passwords['C5A'],'csrfmiddlewaretoken':token}).status_code,302)
  self.assertEqual(csrf.post(url,{'attempt':1}).status_code,403)
  c=self.logged('C5A')
  self.assertEqual(c.post(url,{'attempt':2}).status_code,409)
  for state in ('queued','running','failed'):
   ImportJob.objects.filter(pk=j.pk).update(status=state)
   self.assertEqual(c.post(url,{'attempt':1}).status_code,409)
  self.assertFalse(ProblemVersion.objects.exists())
 def test_missing_publish_grant_and_revoked_import_reject(self):
  j=self.job();Grant.objects.filter(user=j.owner,capability='problems.publish').update(revoked=True)
  with self.assertRaises(PermissionDenied):pub.publish(j.owner,j.pk,1)
  Grant.objects.filter(user=j.owner,capability='problems.publish').update(revoked=False)
  Grant.objects.filter(user=j.owner,capability='problems.import').update(revoked=True)
  with self.assertRaises(PermissionDenied):pub.publish(j.owner,j.pk,1)
  self.assertFalse(ProblemVersion.objects.exists())
 def test_filesystem_failure_preserves_previous_and_recovers(self):
  oldjob=self.job();old=pub.publish(oldjob.owner,oldjob.pk,1);original=pub.file_manifest(pub.destination(old))
  j=self.job(unique=True)
  with patch.object(pub,'install_directory',side_effect=OSError('injected disk failure')):
   with self.assertRaises(OSError):pub.publish(j.owner,j.pk,1)
  v=ProblemVersion.objects.get(job=j);self.assertEqual(v.state,'preparing');self.assertIsNone(v.problem_id)
  self.assertFalse(pub.destination(v).exists());self.assertEqual(pub.file_manifest(pub.destination(old)),original)
  v=pub.publish(j.owner,j.pk,1);self.assertTrue(pub.verify_native(v));self.assertTrue(pub.verify_native(old));self.assertNotEqual(old.code,v.code)
 def test_db_failure_after_rename_rolls_back_native_and_recovery_reuses_bytes(self):
  j=self.job()
  with patch.object(Audit.objects,'create',side_effect=IntegrityError('injected DB failure')):
   with self.assertRaises(IntegrityError):pub.publish(j.owner,j.pk,1)
  v=ProblemVersion.objects.get(job=j);self.assertTrue(pub.destination(v).exists());self.assertFalse(Problem.objects.filter(code=v.code).exists())
  inode=(pub.destination(v)/'data.zip').stat().st_ino
  v=pub.publish(j.owner,j.pk,1);self.assertEqual((pub.destination(v)/'data.zip').stat().st_ino,inode);self.assertTrue(pub.verify_native(v))
 def test_crash_after_rename_is_durably_recoverable_in_a_new_process(self):
  j=self.job();script='''import os,sys,django
os.environ['DJANGO_SETTINGS_MODULE']='dmoj.cpj_integration_settings'
django.setup()
from django.conf import settings
from django.db import connections
settings.CPJ_IMPORT_ROOT=sys.argv[1]
connections['default'].close();connections['default'].settings_dict['NAME']=sys.argv[2]
from django.contrib.auth import get_user_model
from cpjudge import publication as p
p.finalize=lambda *args:os._exit(72)
p.publish(get_user_model().objects.get(pk=int(sys.argv[3])),int(sys.argv[4]),1)
'''
  child=subprocess.run([sys.executable,'-c',script,self.temp.name,connection.settings_dict['NAME'],str(j.owner_id),str(j.pk)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
  self.assertEqual(child.returncode,72,child.stdout.decode())
  v=ProblemVersion.objects.get(job=j);self.assertTrue(v.manifest);self.assertEqual(v.state,'preparing');self.assertTrue(pub.verify_files(v));self.assertIsNone(v.problem_id)
  from django.core.management import call_command
  call_command('recover_publications',v.pk,stdout=io.StringIO());v.refresh_from_db();self.assertTrue(pub.verify_native(v))
 def test_crash_before_rename_and_partial_staging_do_not_create_native_problem(self):
  j=self.job()
  class Interrupted(BaseException):pass
  with patch.object(pub,'install_directory',side_effect=Interrupted):
   with self.assertRaises(Interrupted):pub.publish(j.owner,j.pk,1)
  v=ProblemVersion.objects.get(job=j);orphan=pub.root()/('.'+v.code+'-orphan');orphan.mkdir();(orphan/'partial').write_bytes(b'partial')
  self.assertFalse(Problem.objects.filter(code=v.code).exists());self.assertIsNone(v.problem_id)
  v=pub.publish(j.owner,j.pk,1);self.assertTrue(pub.verify_native(v));self.assertTrue(orphan.exists())
 def test_concurrent_requests_cannot_double_publish(self):
  j=self.job();entered=threading.Event();release=threading.Event();original=pub.prepare
  def held(*args):entered.set();self.assertTrue(release.wait(10));return original(*args)
  def publish_thread():
   close_old_connections()
   try:return pub.publish(get_user_model().objects.get(pk=j.owner_id),j.pk,1).pk
   finally:close_old_connections()
  with patch.object(pub,'prepare',side_effect=held),ThreadPoolExecutor(1) as pool:
   future=pool.submit(publish_thread);self.assertTrue(entered.wait(10))
   try:
    with self.assertRaisesRegex(pub.PublicationError,'in progress'):pub.publish(j.owner,j.pk,1)
   finally:release.set()
   first=future.result(20)
  self.assertEqual(pub.publish(j.owner,j.pk,1).pk,first);self.assertEqual(ProblemVersion.objects.count(),1)
  self.assertEqual(Audit.objects.filter(action='problem.publish').count(),1)
 def test_installed_or_native_tampering_fails_closed_without_overwrite(self):
  j=self.job();v=pub.publish(j.owner,j.pk,1);path=pub.destination(v)/'checker.cpp';original=path.read_bytes();path.chmod(0o600);path.write_bytes(b'changed')
  with self.assertRaises(pub.PublicationError):pub.publish(j.owner,j.pk,1)
  self.assertFalse(pub.published_access(j.owner,v.problem));self.assertEqual(path.read_bytes(),b'changed')
  path.write_bytes(original);path.chmod(0o444);Problem.objects.filter(pk=v.problem_id).update(time_limit=9)
  v.refresh_from_db()
  with self.assertRaises(pub.PublicationError):pub.verify_native(v)
 def test_unfinished_all_versions_no_submission_or_private_data_routes(self):
  j=self.job();v=pub.publish(j.owner,j.pk,1);c=self.logged('C5A');base='/problem/'+v.code
  self.assertEqual(c.get(base).status_code,200)
  for method in ('get','post'):self.assertEqual(getattr(c,method)(base+'/submit').status_code,403)
  with self.assertRaises(PermissionDenied):Submission(problem=v.problem).judge()
  for name in ('data.zip','init.yml','checker.cpp','raw.zip','statement.html','../data.zip','%2e%2e%2fdata.zip'):
   self.assertIn(c.get(base+'/published-assets/'+name).status_code,(400,403,404))
  asset=base+'/published-assets/statement.css';self.assertEqual(c.get(asset).status_code,200)
  for client in (Client(),self.logged('C5B'),self.logged('C5P')):
   self.assertIn(client.get(base).status_code,(401,403,404));self.assertIn(client.get(asset).status_code,(401,403,404))
  ProblemVersion.objects.filter(pk=v.pk).update(state='preparing')
  self.assertEqual(c.get(base).status_code,404);self.assertEqual(c.get(asset).status_code,404)
 def test_source_mapping_tampering_or_sanitization_failure_cannot_publish(self):
  j=self.job();base=attempt_path(j.token)/'output';config_path=base/j.findings['slug']/'init.yml';config=yaml.safe_load(config_path.read_text());config['test_cases'][0]['in']='2.in';config_path.write_text(yaml.safe_dump(config))
  with self.assertRaises(pub.PublicationError):pub.publish(j.owner,j.pk,1)
  self.assertFalse(Problem.objects.filter(code__startswith='pv9').exists())
 def test_existing_published_version_survives_later_attempt_failure_and_source_removal(self):
  j=self.job();v=pub.publish(j.owner,j.pk,1)
  ImportJob.objects.filter(pk=j.pk).update(status='failed',attempt=2,token=secrets.token_hex(32),findings={})
  (private_root()/j.archive_key).unlink();shutil.rmtree(attempt_path(j.token))
  self.assertTrue(pub.verify_native(v));self.assertTrue(pub.published_access(j.owner,v.problem))
  with self.assertRaises(pub.PublicationError):pub.publish(j.owner,j.pk,2)

 def test_fsync_failure_leaves_no_native_or_final_directory_and_retry_recovers(self):
  j=self.job()
  with patch('tools.site_problem.os.fsync',side_effect=OSError('injected fsync failure')):
   with self.assertRaises(OSError):pub.publish(j.owner,j.pk,1)
  v=ProblemVersion.objects.get(job=j)
  self.assertIsNone(v.problem_id);self.assertFalse(pub.destination(v).exists())
  self.assertTrue(pub.verify_native(pub.publish(j.owner,j.pk,1)))
 def test_revocation_during_prepare_prevents_finalization_and_recovery(self):
  j=self.job();original=pub.prepare
  def revoked(*args):
   result=original(*args);Grant.objects.filter(user=j.owner,capability='problems.publish').update(revoked=True);return result
  with patch.object(pub,'prepare',side_effect=revoked):
   with self.assertRaises(PermissionDenied):pub.publish(j.owner,j.pk,1)
  v=ProblemVersion.objects.get(job=j);self.assertIsNone(v.problem_id);self.assertTrue(pub.destination(v).exists())
  with self.assertRaises(PermissionDenied):pub.publish(j.owner,j.pk,1)
  Grant.objects.filter(user=j.owner,capability='problems.publish').update(revoked=False)
  self.assertTrue(pub.verify_native(pub.publish(j.owner,j.pk,1)))

 def test_extra_native_execution_fields_and_archive_escape_are_rejected(self):
  j=self.job();path=attempt_path(j.token)/'output'/j.findings['slug']/'init.yml';original=yaml.safe_load(path.read_text())
  from copy import deepcopy
  for kind in ('archive','generator','case-checker','checker-args'):
   config=deepcopy(original)
   if kind=='archive':config['archive']='../other/data.zip'
   elif kind=='generator':config['generator']='checker.cpp'
   elif kind=='case-checker':config['test_cases'][0]['checker']='custom'
   else:config['checker']['args']['flags']=['-DCHANGED']
   path.write_text(yaml.safe_dump(config))
   with self.assertRaises(pub.PublicationError):pub.publish(j.owner,j.pk,1)
  self.assertFalse(Problem.objects.filter(code__startswith='pv9').exists())

 def test_outer_transaction_cannot_defer_intent_commit_past_filesystem_install(self):
  from django.db import transaction
  j=self.job()
  with transaction.atomic():
   with self.assertRaises(RuntimeError):pub.publish(j.owner,j.pk,1)
  self.assertFalse(ProblemVersion.objects.exists())

 def test_actual_http_publication_can_commit_durable_phases(self):
  j=self.job();c=self.logged('C5A')
  response=c.post(f'/imports/{j.pk}/publish/',{'attempt':1})
  self.assertEqual(response.status_code,302)
  v=ProblemVersion.objects.get(job=j);self.assertTrue(pub.verify_native(v))
  self.assertEqual(c.post(f'/imports/{j.pk}/publish/',{'attempt':1}).status_code,302)
  self.assertEqual(ProblemVersion.objects.filter(job=j).count(),1)
 def test_replaced_session_during_http_staging_cannot_finalize(self):
  from cpjudge.models import Identity
  from django.db.models import F
  j=self.job();c=self.logged('C5A');original=pub.prepare
  def replaced(*args):
   result=original(*args)
   Identity.objects.filter(user=j.owner).update(generation=F('generation')+1)
   return result
  with patch.object(pub,'prepare',side_effect=replaced):
   self.assertEqual(c.post(f'/imports/{j.pk}/publish/',{'attempt':1}).status_code,403)
  v=ProblemVersion.objects.get(job=j);self.assertIsNone(v.problem_id);self.assertEqual(v.state,'preparing')
  self.assertFalse(Problem.objects.filter(code=v.code).exists())
