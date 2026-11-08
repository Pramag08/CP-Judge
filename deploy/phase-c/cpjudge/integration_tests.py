"""Real native URL/admin/widget/task integration against isolated MariaDB."""
import datetime,json,secrets,tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import IntegrityError,transaction
from django.test import TestCase,Client
from django.utils import timezone
from cpjudge.identity import provision,correct_id,reset
from cpjudge.models import Identity,Grant,ExportJob,Conflict,CollegeIDHistory,Audit
from cpjudge.policy import grant_scope

U=get_user_model()

class NativeIntegrationTests(TestCase):
 def setUp(self):
  from judge.models import Contest,Problem,ProblemGroup,ContestProblem,Profile,Language,Submission,SubmissionSource,ContestParticipation
  cache.clear()
  self.admin=U.objects.create_superuser('c1operator',password='Test-operator-752!')
  Profile.objects.get_or_create(user=self.admin)
  self.users={};self.passwords={}
  for cid,author in [('C1A',True),('C1B',True),('C1P',False),('C1Q',False)]:
   user,password=provision(self.admin,cid,email=cid.lower()+'@private.invalid',author=author)
   Identity.objects.filter(user=user).update(must_change_password=False)
   self.users[cid]=user;self.passwords[cid]=password
  now=timezone.now()
  self.a=Contest.objects.create(key='c1a',name='A private',start_time=now-datetime.timedelta(hours=1),end_time=now+datetime.timedelta(hours=2),is_visible=True,is_private=True,format_name='cpjudge_icpc_v1')
  self.b=Contest.objects.create(key='c1b',name='B private',start_time=self.a.start_time,end_time=self.a.end_time,is_visible=True,is_private=True,format_name='cpjudge_icpc_v1')
  for c,cid in [(self.a,'C1A'),(self.b,'C1B')]:
   for cap in ('settings.edit','roster.read','roster.export','submissions.review','source.review','grants.manage'):
    grant_scope(self.admin,self.users[cid],c,cap)
  self.a.private_contestants.add(self.users['C1P'].profile)
  self.b.private_contestants.add(self.users['C1Q'].profile)
  for c,cid in [(self.a,'C1P'),(self.b,'C1Q')]:ContestParticipation.objects.create(contest=c,user=self.users[cid].profile)
  group=ProblemGroup.objects.create(name='C1',full_name='C1 test')
  self.language=Language.objects.create(key='C1CPP',name='C1 C++',short_name='C++',common_name='C++',extension='cpp',ace='c_cpp',pygments='cpp')
  self.problem=Problem.objects.create(code='c1private',name='C1 problem',description='Private problem',group=group,time_limit=1,memory_limit=65536,points=1,is_public=False,is_manually_managed=True)
  self.problem.allowed_languages.add(self.language)
  ContestProblem.objects.create(contest=self.a,problem=self.problem,points=1,order=0)
  self.sub=Submission.objects.create(user=self.users['C1P'].profile,problem=self.problem,language=self.language,status='D',result='AC',time=0.1,memory=1024,points=1,case_points=1,case_total=1,contest_object=self.a)
  SubmissionSource.objects.create(submission=self.sub,source='int main(){}')

 def login(self,cid,client=None):
  client=client or self.client
  r=client.post('/accounts/login/',{'username':cid,'password':self.passwords[cid]})
  self.assertEqual(r.status_code,302)
  return client

 def test_native_cross_contest_roster_admin_files_and_source(self):
  c=self.login('C1A')
  self.assertContains(c.get('/contest/c1a/roster'),'c1p@private.invalid')
  for url in ('/contest/c1b','/contest/c1b/roster','/contest/c1b/roster/export',f'/admin/judge/contest/{self.b.pk}/change/'):
   self.assertIn(c.get(url).status_code,(403,404))
  self.assertNotContains(c.get('/admin/judge/contest/'),'B private')
  self.assertEqual(c.get('/src/'+str(self.sub.pk)+'/raw').status_code,200)
  for url in ('/problem/c1private/test_data','/problem/c1private/data/init.yml','/admin/judge/problem/','/admin/auth/user/','/api/v2/users','/data/download/'):
   self.assertIn(c.get(url).status_code,(403,404))

 def test_participant_and_account_admin_have_no_author_default(self):
  c=self.login('C1P')
  for url in ('/contest/c1a/roster','/admin/','/admin/judge/contest/'):
   self.assertIn(c.get(url).status_code,(403,404))
  c=Client();c.post('/accounts/login/',{'username':'c1operator','password':'Test-operator-752!'})
  self.assertEqual(c.get('/admin/auth/user/').status_code,200)
  for url in ('/contest/c1a/roster','/src/'+str(self.sub.pk)+'/raw','/problem/c1private/test_data'):
   self.assertIn(c.get(url).status_code,(403,404))
  self.assertIn(c.get('/admin/judge/contest/').status_code,(403,404))

 def test_ajax_shortcircuit_and_sources_use_current_session_and_scope(self):
  outsider=self.login('C1Q')
  for url in (f'/widgets/submission_testcases?id={self.sub.pk}',f'/widgets/single_submission?id={self.sub.pk}',f'/src/{self.sub.pk}/raw'):
   self.assertEqual(outsider.get(url).status_code,404)
  owner=self.login('C1P',Client());replacement=self.login('C1P',Client())
  self.assertEqual(owner.get(f'/widgets/submission_testcases?id={self.sub.pk}').status_code,401)
  self.assertEqual(replacement.get(f'/widgets/single_submission?id={self.sub.pk}').status_code,200)

 def test_events_anonymous_cross_scope_and_replaced_session(self):
  path='/cpjudge/events/sub_'+self.sub.id_secret
  self.assertEqual(self.client.get(path).status_code,401)
  outsider=self.login('C1Q')
  self.assertEqual(outsider.get(path).status_code,404)
  owner=self.login('C1P',Client())
  self.assertEqual(owner.get(path).status_code,200)
  self.assertEqual(owner.get('/cpjudge/events/tickets').status_code,404)
  self.login('C1P',Client())
  self.assertEqual(owner.get(path).status_code,401)

 def test_event_and_source_revoked_grant(self):
  c=self.login('C1A')
  self.assertEqual(c.get('/cpjudge/events/sub_'+self.sub.id_secret).status_code,200)
  Grant.objects.filter(user=self.users['C1A']).update(revoked=True)
  self.assertEqual(c.get('/cpjudge/events/sub_'+self.sub.id_secret).status_code,404)
  self.assertEqual(c.get('/src/'+str(self.sub.pk)+'/raw').status_code,404)

 def test_native_lists_do_not_expose_unrelated_attempts_or_email(self):
  c=self.login('C1Q')
  data=c.get('/cpjudge/events/submissions').json()
  self.assertEqual(data['messages'],[])
  response=c.get('/submissions/')
  self.assertNotContains(response,'c1p@private.invalid')
  self.assertNotContains(response,'submission/'+str(self.sub.pk)+'"')
  response=self.login('C1P',Client()).get('/contest/c1a/ranking/')
  self.assertNotContains(response,'c1q@private.invalid')

 def test_native_profile_round_trip_is_owned(self):
  c=self.login('C1P')
  response=c.post('/edit/profile/',{'first_name':'New','last_name':'Name','email':'own@private.invalid','id':self.users['C1Q'].pk})
  self.assertEqual(response.status_code,302)
  self.users['C1P'].refresh_from_db();self.users['C1Q'].refresh_from_db()
  self.assertEqual(self.users['C1P'].email,'own@private.invalid')
  self.assertEqual(self.users['C1Q'].email,'c1q@private.invalid')

 def test_export_worker_and_download_recheck_scope_generation_and_owner(self):
  from cpjudge.tasks import export_roster,EXPORT_ROOT
  c=self.login('C1A');identity=Identity.objects.get(user=self.users['C1A'])
  job=ExportJob.objects.create(owner=self.users['C1A'],contest=self.a,generation=identity.generation,token=secrets.token_hex(24))
  with tempfile.TemporaryDirectory() as tmp,patch('cpjudge.tasks.EXPORT_ROOT',__import__('pathlib').Path(tmp)):
   export_roster.run(job.pk)
   self.assertEqual(c.get('/cpjudge/exports/'+job.token).status_code,200)
   self.assertEqual(self.login('C1B',Client()).get('/cpjudge/exports/'+job.token).status_code,404)
   grant_scope(self.admin,self.users['C1A'],self.a,'roster.export',revoke=True)
   self.assertEqual(c.get('/cpjudge/exports/'+job.token).status_code,403)
   with self.assertRaises(PermissionDenied):export_roster.run(job.pk)
   job.refresh_from_db();self.assertEqual(job.status,'denied')

 def test_legacy_unsafe_tasks_reject_missing_or_forged_scope(self):
  from judge.tasks import prepare_user_data,rescore_contest,rejudge_problem_filter
  for task,args in ((prepare_user_data,(self.users['C1P'].profile.pk,'{}')),(rescore_contest,('c1a',)),(rejudge_problem_filter,(self.problem.pk,))):
   with self.subTest(task=task.name),self.assertRaises(PermissionDenied):task.run(*args)

 def test_audited_correction_preserves_password_username_and_rejects_collisions(self):
  user=self.users['C1P'];old_password=user.password;old_username=user.username
  c=self.login('C1P')
  correct_id(self.admin,user.pk,' corrected01 ','Registrar approved correction')
  user.refresh_from_db();self.assertEqual(user.password,old_password);self.assertEqual(user.username,old_username)
  self.assertEqual(c.get('/edit/profile/').status_code,401)
  self.assertEqual(Client().post('/accounts/login/',{'username':'CORRECTED01','password':self.passwords['C1P']}).status_code,302)
  self.assertTrue(Audit.objects.filter(action='college_id.correct',subject=user,actor=self.admin).exists())
  with self.assertRaises(ValidationError):correct_id(self.admin,self.users['C1Q'].pk,'C1P','Conflicting correction')
  with self.assertRaises((ValidationError,IntegrityError)),transaction.atomic():provision(self.admin,'C1P')

 def test_legacy_account_preserved_until_explicit_id_assignment(self):
  from judge.models import Profile
  legacy=U.objects.create_user('legacy.user',password='Legacy-password-794!');Profile.objects.create(user=legacy)
  before=legacy.password
  self.assertEqual(Client().post('/accounts/login/',{'username':'legacy.user','password':'Legacy-password-794!'}).status_code,302)
  self.assertIsNone(Identity.objects.get(user=legacy).college_id)
  correct_id(self.admin,legacy.pk,'COLLEGE123','Verified college registrar record')
  legacy.refresh_from_db();self.assertEqual(legacy.password,before)

 def test_conflict_flag_survives_revocation_and_native_join_is_unranked(self):
  self.assertTrue(Conflict.objects.filter(user=self.users['C1A'],contest=self.a).exists())
  grant_scope(self.admin,self.users['C1A'],self.a,'source.review',revoke=True)
  self.assertTrue(Conflict.objects.filter(user=self.users['C1A'],contest=self.a).exists())
  c=self.login('C1A')
  self.assertEqual(c.post('/contest/c1a/join').status_code,302)
  self.users['C1A'].profile.refresh_from_db()
  self.assertEqual(self.users['C1A'].profile.current_contest.virtual,-1)
  Grant.objects.filter(user=self.users['C1A']).update(revoked=True)
  self.a.private_contestants.add(self.users['C1A'].profile)
  self.assertEqual(c.post('/contest/c1a/join').status_code,302)
  self.assertFalse(self.a.users.filter(user=self.users['C1A'].profile,virtual=0).exists())

 def test_native_reset_password_change_logout_and_stale_logout(self):
  a=self.login('C1P',Client());b=self.login('C1P',Client())
  self.assertEqual(a.post('/accounts/logout/').status_code,401)
  self.assertEqual(b.get('/edit/profile/').status_code,200)
  _,temporary=reset(self.admin,'C1P')
  self.assertEqual(b.get('/edit/profile/').status_code,401)
  c=Client();r=c.post('/accounts/login/',{'username':'C1P','password':temporary})
  self.assertEqual(r.url,'/accounts/password/change/')
  self.assertEqual(c.get('/cpjudge/events/submissions').status_code,302)
  r=c.post('/accounts/password/change/',{'old_password':temporary,'new_password1':'Native-new-password-739!', 'new_password2':'Native-new-password-739!'})
  self.assertEqual(r.status_code,302)
  self.assertEqual(c.get('/edit/profile/').status_code,200)
  self.assertEqual(c.post('/accounts/logout/').status_code,200)
  self.assertEqual(c.get('/cpjudge/events/submissions').status_code,401)

 def test_native_author_create_and_own_edit(self):
  from judge.models import Contest
  c=self.login('C1A')
  response=c.post('/admin/judge/contest/add/',{'key':'c1created','name':'Owner draft','description':'Draft',
       'start_time_0':'2027-01-01','start_time_1':'10:00:00','end_time_0':'2027-01-01','end_time_1':'11:00:00','_save':'Save'})
  self.assertEqual(response.status_code,302)
  obj=Contest.objects.get(key='c1created')
  self.assertTrue(Grant.objects.filter(user=self.users['C1A'],contest=obj,capability='roster.read',revoked=False).exists())
  self.assertEqual(c.get(f'/admin/judge/contest/{obj.pk}/change/').status_code,200)
  self.assertEqual(self.login('C1B',Client()).post(f'/admin/judge/contest/{obj.pk}/change/',{'name':'Stolen'}).status_code,404)

 def test_native_hidden_case_feedback_is_not_delivered(self):
  from judge.models import SubmissionTestCase
  SubmissionTestCase.objects.create(submission=self.sub,case=1,status='WA',time=0.1,memory=1,points=0,total=1,
      output='PRIVATE PROGRAM OUTPUT',feedback='PRIVATE CHECKER FEEDBACK',extended_feedback='PRIVATE EXPECTED VALUE')
  c=self.login('C1P')
  for url in (f'/submission/{self.sub.pk}',f'/widgets/submission_testcases?id={self.sub.pk}'):
   response=c.get(url)
   self.assertEqual(response.status_code,200)
   for private in ('PRIVATE PROGRAM OUTPUT','PRIVATE CHECKER FEEDBACK','PRIVATE EXPECTED VALUE'):
    self.assertNotContains(response,private)
  self.assertEqual(SubmissionTestCase.objects.get(submission=self.sub).output,'PRIVATE PROGRAM OUTPUT')

 def test_stored_case_numbers_and_skipped_label(self):
  from judge.models import SubmissionTestCase
  SubmissionTestCase.objects.create(submission=self.sub,case=2,status='AC',time=0.1,memory=1,points=1,total=1)
  SubmissionTestCase.objects.create(submission=self.sub,case=7,status='SC',points=0,total=1)
  c=self.login('C1P')
  for url in (f'/submission/{self.sub.pk}',f'/widgets/submission_testcases?id={self.sub.pk}'):
   response=c.get(url)
   self.assertContains(response,'Test case #2:')
   self.assertContains(response,'Test case #7:')
   self.assertContains(response,'Skipped (not run)')
   self.assertNotContains(response,'Test case #1:')

 def test_own_contest_list_pagination_scope_and_empty_message(self):
  from judge.models import Submission
  owner=self.login('C1P')
  path='/contest/c1a/my-submissions/'
  for _ in range(51):
   Submission.objects.create(user=self.users['C1P'].profile,problem=self.problem,language=self.language,
       status='D',result='AC',contest_object=self.a,time=0.1,memory=1024,points=1,case_points=1,case_total=1)
  first=owner.get(path)
  second=owner.get(path+'?page=2')
  self.assertEqual(first.status_code,200)
  self.assertEqual(second.status_code,200)
  self.assertEqual(first.context['page_obj'].number,1)
  self.assertEqual(second.context['page_obj'].number,2)
  self.assertEqual(len(first.context['submissions']),50)
  self.assertEqual(len(second.context['submissions']),2)
  filtered=owner.get(path+'?status=WA')
  self.assertContains(filtered,'No submissions match this contest and filter yet.')
  self.assertNotContains(filtered,f'/submission/{self.sub.pk}')

 def test_no_worker_submit_form_does_not_claim_verdict(self):
  c=self.login('C1P')
  response=c.get('/problem/c1private/submit')
  self.assertContains(response,'No judge is available for this problem.')
  self.assertNotContains(response,'Submit!')

 def test_queued_submission_shows_waiting_not_accepted(self):
  self.sub.status='QU';self.sub.result='';self.sub.case_points=0;self.sub.save(update_fields=['status','result','case_points'])
  response=self.login('C1P').get(f'/submission/{self.sub.pk}')
  self.assertContains(response,'waiting for a suitable judge')
  self.assertNotContains(response,'Test case #1:')

 def test_reset_rate_limit_and_login_rechecks_corrected_id(self):
  for _ in range(10):reset(self.admin,'C1P')
  with self.assertRaises(ValidationError):reset(self.admin,'C1P')
  from cpjudge.identity import CollegeBackend
  old_auth=CollegeBackend.authenticate
  calls=[0]
  def racing_auth(backend,request,username=None,password=None,**kwargs):
   result=old_auth(backend,request,username=username,password=password,**kwargs)
   calls[0]+=1
   if calls[0]==1 and result:
    correct_id(self.admin,result.pk,'C1RACECORRECT','Correction committed before login admission')
   return result
  with patch.object(CollegeBackend,'authenticate',racing_auth):
   r=Client().post('/accounts/login/',{'username':'C1Q','password':self.passwords['C1Q']})
  self.assertEqual(r.status_code,200)
  self.assertContains(r,'id="form-errors"')

 def test_scoped_delegate_admin_and_roster_only_conflict_policy(self):
  p=self.users['C1P']
  grant_scope(self.admin,p,self.a,'roster.read')
  self.assertFalse(Conflict.objects.filter(user=p,contest=self.a).exists())
  grant_scope(self.admin,p,self.a,'settings.edit')
  c=self.login('C1P')
  self.assertEqual(c.get(f'/admin/judge/contest/{self.a.pk}/change/').status_code,200)
  self.assertEqual(c.get(f'/admin/judge/contest/{self.b.pk}/change/').status_code,404)
  self.assertEqual(c.get('/admin/judge/contest/add/').status_code,403)


from cpjudge.tests import ConcurrencyTests
class NativeRaceTests(ConcurrencyTests):
 def test_inflight_request_serializes_replacement_login(self):
  import threading,time
  from concurrent.futures import ThreadPoolExecutor
  from django.db import close_old_connections
  from django.test import RequestFactory
  from importlib import import_module
  from django.conf import settings
  from django.http import HttpResponse
  from cpjudge.sessions import GenerationMiddleware
  user,password=provision(self.admin,'LOCKRACE')
  Identity.objects.filter(user=user).update(must_change_password=False)
  client=Client();client.post('/accounts/login/',{'username':'LOCKRACE','password':password})
  key=client.cookies[settings.SESSION_COOKIE_NAME].value
  entered=threading.Event();release=threading.Event()
  def request():
   close_old_connections()
   try:
    req=RequestFactory().get('/edit/profile/')
    req.user=U.objects.get(pk=user.pk)
    req.session=import_module(settings.SESSION_ENGINE).SessionStore(session_key=key)
    def view(r):
     entered.set();release.wait(10)
     return HttpResponse('admitted')
    return GenerationMiddleware(view)(req).status_code
   finally:close_old_connections()
  def login():
   close_old_connections()
   try:
    c=Client();r=c.post('/accounts/login/',{'username':'LOCKRACE','password':password})
    return c,r.status_code
   finally:close_old_connections()
  with ThreadPoolExecutor(2) as pool:
   a=pool.submit(request);self.assertTrue(entered.wait(10))
   b=pool.submit(login)
   time.sleep(0.1);self.assertFalse(b.done())
   release.set();self.assertEqual(a.result(timeout=10),200)
   replacement,status=b.result(timeout=10);self.assertEqual(status,302)
  self.assertEqual(client.get('/edit/profile/').status_code,401)
  self.assertEqual(replacement.get('/edit/profile/').status_code,200)

 def test_dispatch_waits_for_durable_commit_and_drops_rolled_back_admission(self):
  from judge.models import ProblemGroup,Problem,Language,Submission,SubmissionSource
  user,_=provision(self.admin,'COMMIT01')
  group=ProblemGroup.objects.create(name='commit',full_name='Commit test')
  problem=Problem.objects.create(code='commit01',name='Commit',description='x',group=group,time_limit=1,memory_limit=65536,points=1)
  language=Language.objects.create(key='CMTCPP',name='Commit CPP',short_name='CPP',common_name='CPP',extension='cpp',ace='c_cpp',pygments='cpp')
  with patch('judge.models.submission.judge_submission') as dispatch:
   with transaction.atomic():
    sub=Submission.objects.create(user=user.profile,problem=problem,language=language)
    SubmissionSource.objects.create(submission=sub,source='int main(){}')
    sub.judge(force_judge=True)
    dispatch.assert_not_called()
   dispatch.assert_called_once()
   dispatch.reset_mock()
   with self.assertRaises(ValueError):
    with transaction.atomic():
     sub.judge(force_judge=True)
     raise ValueError('Rollback admission')
   dispatch.assert_not_called()

 def test_concurrent_correction_reserves_one_owner_without_merging(self):
  import threading
  from concurrent.futures import ThreadPoolExecutor
  from django.db import close_old_connections
  a,_=provision(self.admin,'CORRA');b,_=provision(self.admin,'CORRB')
  barrier=threading.Barrier(2)
  def attempt(pk):
   close_old_connections()
   try:
    actor=U.objects.get(pk=self.admin.pk);barrier.wait(timeout=10)
    try:
     correct_id(actor,pk,'SAMECORR','Concurrent registrar correction test')
     return 'corrected'
    except (ValidationError,IntegrityError):return 'collision'
   finally:close_old_connections()
  with ThreadPoolExecutor(2) as pool:results=list(pool.map(attempt,[a.pk,b.pk]))
  self.assertCountEqual(results,['corrected','collision'])
  self.assertEqual(Identity.objects.filter(college_id='SAMECORR').count(),1)
  self.assertEqual(CollegeIDHistory.objects.filter(college_id='SAMECORR').count(),1)
  a.refresh_from_db();b.refresh_from_db()
  self.assertEqual((a.username,b.username),('CORRA','CORRB'))


class NativeUploadHTTPTests(TestCase):
 def setUp(self):
  import tempfile
  from django.test import override_settings
  from judge.models import Contest,Profile
  from cpjudge.policy import grant_scope
  self.temp=tempfile.TemporaryDirectory(prefix='cpj-c05-')
  self.addCleanup(self.temp.cleanup)
  override=override_settings(CPJ_IMPORT_ROOT=self.temp.name,CPJ_ARCHIVE_LIMITS={'upload_bytes':1024})
  override.enable();self.addCleanup(override.disable)
  self.admin=U.objects.create_superuser('c5admin',password='Test-c5-admin-417!')
  Profile.objects.get_or_create(user=self.admin)
  self.users={};self.passwords={}
  self.passwords['c5admin']='Test-c5-admin-417!'
  for cid,author in [('C5A',True),('C5B',True),('C5P',False)]:
   user,password=provision(self.admin,cid,author=author)
   Identity.objects.filter(user=user).update(must_change_password=False)
   self.users[cid]=user;self.passwords[cid]=password
  now=timezone.now()
  self.contests={}
  for key,cid in [('c5a','C5A'),('c5b','C5B')]:
   obj=Contest.objects.create(key=key,name=key.upper(),start_time=now-datetime.timedelta(hours=1),end_time=now+datetime.timedelta(hours=1),is_visible=True,is_private=True,format_name='cpjudge_icpc_v1')
   grant_scope(self.admin,self.users[cid],obj,'problems.import')
   self.contests[key]=obj
  self.contests['c5a'].private_contestants.add(self.users['C5P'].profile)

 def zip_bytes(self):
  import io,zipfile
  out=io.BytesIO()
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
   info=zipfile.ZipInfo('package-info.txt',(2020,1,1,0,0,0))
   archive.writestr(info,'test-only C05 upload')
  return out.getvalue()

 def logged(self,cid,client=None):
  from django.test import Client
  client=client or Client()
  response=client.post('/accounts/login/',{'username':cid,'password':self.passwords[cid]})
  self.assertEqual(response.status_code,302)
  return client

 def upload_file(self,data=None,name='valid.zip'):
  from django.core.files.uploadedfile import SimpleUploadedFile
  return SimpleUploadedFile(name,data if data is not None else self.zip_bytes(),content_type='application/zip')

 def files_and_records(self):
  from pathlib import Path
  from cpjudge.models import ImportJob
  root=Path(self.temp.name)
  return list(root.iterdir()) if root.exists() else [],ImportJob.objects.count()

 def test_author_single_zip_confirmation_refresh_download_and_public_denial(self):
  from cpjudge.models import ImportJob
  client=self.logged('C5A')
  page=client.get('/contest/c5a/import/')
  self.assertEqual(page.status_code,200)
  self.assertContains(page,f'{1024/(1024**2):g} MiB')
  with patch('cpjudge.conversion.queue_conversion') as queued:
   response=client.post('/contest/c5a/import/',{'package':self.upload_file()})
  self.assertEqual(response.status_code,302)
  job=ImportJob.objects.get(owner=self.users['C5A'])
  self.assertEqual(response.url,f'/imports/{job.pk}/')
  queued.assert_called_once_with(self.users['C5A'],job.pk)
  self.assertEqual(job.status,'uploaded');self.assertEqual(job.attempt,0)
  confirm=client.get(response.url);self.assertEqual(confirm.status_code,200)
  self.assertContains(confirm,'Converting ZIP')
  self.assertEqual(client.get(response.url).status_code,200)
  package=client.get(f'/imports/{job.pk}/download/')
  self.assertEqual(package.status_code,200)
  self.assertEqual(b''.join(package.streaming_content),self.zip_bytes())
  self.assertEqual(client.get('/media/'+job.archive_key).status_code,404)
  self.assertEqual(client.get('/static/'+job.archive_key).status_code,404)

 def test_logged_out_participant_other_author_and_admin_cannot_upload_or_inspect(self):
  import datetime
  from cpjudge.models import ImportJob
  from django.test import Client
  self.assertEqual(Client().post('/contest/c5a/import/',{'package':self.upload_file()}).status_code,401)
  participant=self.logged('C5P')
  self.assertEqual(participant.get('/contest/c5a/import/').status_code,404)
  self.assertEqual(participant.post('/contest/c5a/import/',{'package':self.upload_file()}).status_code,404)
  owner=self.logged('C5A',Client());response=owner.post('/contest/c5a/import/',{'package':self.upload_file()})
  job=ImportJob.objects.get(owner=self.users['C5A'])
  other=self.logged('C5B',Client())
  self.assertEqual(other.get(response.url).status_code,404)
  self.assertEqual(other.get(f'/imports/{job.pk}/download/').status_code,404)
  admin=self.logged('c5admin',Client())
  self.assertEqual(admin.post('/contest/c5a/import/',{'package':self.upload_file()}).status_code,404)
  from cpjudge.policy import grant_scope
  grant_scope(self.admin,self.admin,self.contests['c5a'],'problems.import')
  self.assertEqual(admin.post('/contest/c5a/import/',{'package':self.upload_file()}).status_code,302)
  self.assertEqual(ImportJob.objects.filter(owner=self.users['C5A']).count(),1)
  self.assertEqual(ImportJob.objects.filter(owner=self.admin).count(),1)

 def test_csrf_required_and_failed_requests_leave_no_records_or_private_files(self):
  from django.test import Client
  from cpjudge.models import ImportJob
  client=Client(enforce_csrf_checks=True);client.force_login(self.users['C5A'])
  session=client.session;session['cpjudge_generation']=Identity.objects.get(user=self.users['C5A']).generation;session.save()
  self.assertEqual(client.get('/contest/c5a/import/').status_code,200)
  self.assertEqual(client.post('/contest/c5a/import/',{'package':self.upload_file()}).status_code,403)
  token=client.cookies['csrftoken'].value
  self.assertEqual(client.post('/contest/c5a/import/',{'package':self.upload_file(),'csrfmiddlewaretoken':'bad'},HTTP_X_CSRFTOKEN=token).status_code,403)
  self.assertEqual(ImportJob.objects.count(),0)
  self.assertEqual(self.files_and_records()[0],[])

  authorized=self.logged('C5A')
  self.assertEqual(authorized.post('/contest/c5a/import/',{}).status_code,400)
  self.assertEqual(authorized.post('/contest/c5a/import/',{'package':self.upload_file(name='not-a-zip.txt')}).status_code,400)
  garbage=self.upload_file(b'not a ZIP')
  self.assertEqual(authorized.post('/contest/c5a/import/',{'package':garbage}).status_code,400)
  multi=authorized.post('/contest/c5a/import/',{'package':[self.upload_file(),self.upload_file(name='second.zip')]})
  self.assertEqual(multi.status_code,400)
  self.assertContains(multi,'exactly one ZIP file',status_code=400)
  self.assertEqual(ImportJob.objects.count(),0)
  self.assertEqual(self.files_and_records()[0],[])

 def test_oversize_counts_actual_stream_without_trusting_content_length(self):
  from io import BytesIO
  from django.http import HttpResponse
  from django.test import RequestFactory
  from cpjudge.models import ImportJob
  from cpjudge.uploads import UploadBoundaryMiddleware
  client=self.logged('C5A')
  response=client.post('/contest/c5a/import/',{'package':self.upload_file(b'X'*1025,'large.zip')})
  self.assertEqual(response.status_code,413)
  self.assertContains(response,'configured upload limit',status_code=413)
  self.assertEqual(ImportJob.objects.count(),0)
  self.assertEqual(self.files_and_records()[0],[])
  boundary='c5boundary'
  file=b'X'*1025
  body=(b'--'+boundary.encode()+b'\r\nContent-Disposition: form-data; name="package"; filename="oversize.zip"\r\n'
        b'Content-Type: application/zip\r\n\r\n'+file+b'\r\n--'+boundary.encode()+b'--\r\n')
  for declared in (None,'1'):
   request=RequestFactory().generic('POST','/contest/c5a/import/',body,content_type='multipart/form-data; boundary='+boundary)
   request.user=self.users['C5A'];request.META['wsgi.input_terminated']=True
   request.profile=self.users['C5A'].profile
   request.META.pop('CONTENT_LENGTH',None)
   if declared is not None:request.META['CONTENT_LENGTH']=declared
   request._stream=BytesIO(body);request._read_started=False
   def receive(req):
    list(req.FILES.items())
    return HttpResponse('stream limit reached',status=413 if req.cpj_zip_upload_handler.exceeded else 200)
   response=UploadBoundaryMiddleware(receive)(request)
   self.assertEqual(response.status_code,413)
   self.assertContains(response,'stream limit reached',status_code=413)
  self.assertEqual(ImportJob.objects.count(),0)
  self.assertEqual(self.files_and_records()[0],[])

 def test_unframed_request_fails_closed(self):
  from django.http import HttpResponse
  from django.test import RequestFactory
  from cpjudge.uploads import UploadBoundaryMiddleware
  request=RequestFactory().generic('POST','/contest/c5a/import/',b'ignored',content_type='multipart/form-data')
  request.user=self.users['C5A'];request.META.pop('CONTENT_LENGTH',None)
  response=UploadBoundaryMiddleware(lambda req:HttpResponse('unexpected'))(request)
  self.assertEqual(response.status_code,411)

 def test_large_multipart_uses_private_disk_and_cleans_temporary_file(self):
  from django.core.exceptions import ValidationError
  from django.core.files.uploadedfile import TemporaryUploadedFile
  from django.test import override_settings
  from pathlib import Path
  import io,zipfile
  buffer=io.BytesIO()
  with zipfile.ZipFile(buffer,'w',zipfile.ZIP_STORED) as z:z.writestr('payload.bin',b'X'*(2*1024**2))
  seen=[]
  def inspect(user,uploaded,*args,**kwargs):
   self.assertIsInstance(uploaded,TemporaryUploadedFile)
   path=Path(uploaded.temporary_file_path())
   self.assertTrue(path.is_file())
   self.assertEqual(path.parent,Path('/tmp'))
   seen.append(path)
   raise ValidationError('intentional test rejection')
  with override_settings(CPJ_ARCHIVE_LIMITS={'upload_bytes':3*1024**2}),patch('cpjudge.imports.upload',side_effect=inspect):
   response=self.logged('C5A').post('/contest/c5a/import/',{'package':self.upload_file(buffer.getvalue())})
  self.assertEqual(response.status_code,400)
  self.assertEqual(len(seen),1)
  self.assertFalse(seen[0].exists())

 def test_collision_and_database_failure_preserve_existing_files(self):
  from pathlib import Path
  from cpjudge.imports import upload
  from cpjudge.models import ImportJob
  from django.db import DatabaseError
  root=Path(self.temp.name);existing=root/('collision.zip')
  existing.write_bytes(b'existing private data')
  with patch('cpjudge.imports.secrets.token_hex',return_value='collision'):
   with self.assertRaises(FileExistsError):
    upload(self.users['C5A'],self.upload_file(),self.contests['c5a'],validate_archive=True)
  self.assertEqual(existing.read_bytes(),b'existing private data')
  existing.unlink()
  with patch.object(ImportJob.objects,'create',side_effect=DatabaseError('injected failure')):
   with self.assertRaises(DatabaseError):
    upload(self.users['C5A'],self.upload_file(),self.contests['c5a'],validate_archive=True)
  self.assertEqual(self.files_and_records(),([],0))
  broken=self.upload_file()
  def interrupted(*args,**kwargs):
   yield b'partial bytes'
   raise OSError('private storage failure')
  with patch.object(broken,'chunks',side_effect=interrupted):
   with self.assertRaises(OSError):upload(self.users['C5A'],broken,self.contests['c5a'])
  self.assertEqual(self.files_and_records(),([],0))
  client=self.logged('C5A')
  with patch('cpjudge.imports.upload',side_effect=OSError('/private/internal/path')):
   response=client.post('/contest/c5a/import/',{'package':self.upload_file()})
  self.assertEqual(response.status_code,503)
  self.assertNotContains(response,'/private/internal/path',status_code=503)

 def test_total_body_cap_and_rejected_file_do_not_drain_stream(self):
  from io import BytesIO
  from django.core.exceptions import RequestDataTooBig
  from cpjudge.uploads import BoundedBodyStream,BoundedZipUploadHandler
  from django.core.files.uploadhandler import StopUpload
  source=BytesIO(b'X'*1000000)
  stream=BoundedBodyStream(source,1024)
  with self.assertRaises(RequestDataTooBig):stream.read()
  self.assertEqual(source.tell(),1025)
  handler=BoundedZipUploadHandler(None,1024)
  with self.assertRaises(StopUpload) as raised:handler.receive_data_chunk(b'X'*1025,0)
  self.assertTrue(raised.exception.connection_reset)
  from django.test import RequestFactory
  from cpjudge.uploads import UploadBoundaryMiddleware,MULTIPART_OVERHEAD_LIMIT
  from django.http import HttpResponse
  prefix=b'--limit\r\nContent-Disposition: form-data; name="field"\r\n\r\n'
  payload=prefix+b'X'*1000000+b'\r\n--limit--\r\n'
  request=RequestFactory().generic('POST','/contest/c5a/import/',payload,content_type='multipart/form-data; boundary=limit')
  request.user=self.users['C5A'];request.META.pop('CONTENT_LENGTH',None)
  request.META['wsgi.input_terminated']=True
  source=BytesIO(payload);request._stream=source
  def receive(req):
   list(req.FILES.items())
   return HttpResponse('unexpected')
  with self.assertRaises(RequestDataTooBig):UploadBoundaryMiddleware(receive)(request)
  self.assertLessEqual(source.tell(),1024+MULTIPART_OVERHEAD_LIMIT+1)

 def test_revocation_stale_session_and_owner_deduplication(self):
  from django.test import Client
  from cpjudge.models import ImportJob,Grant
  a=self.logged('C5A')
  url=a.post('/contest/c5a/import/',{'package':self.upload_file()}).url
  self.assertEqual(a.post('/contest/c5a/import/',{'package':self.upload_file()}).url,url)
  self.assertEqual(ImportJob.objects.count(),1)
  job=ImportJob.objects.get()
  self.logged('C5A',Client())
  self.assertEqual(a.post('/contest/c5a/import/',{'package':self.upload_file()}).status_code,401)
  current=self.logged('C5A',Client())
  Grant.objects.filter(user=self.users['C5A'],capability='problems.import').update(revoked=True)
  self.assertIn(current.get(url).status_code,(403,404))
  self.assertIn(current.get(f'/imports/{job.pk}/download/').status_code,(403,404))
  self.assertEqual(current.post('/contest/c5a/import/',{'package':self.upload_file()}).status_code,404)
  self.assertEqual(ImportJob.objects.count(),1)


class NativeExtractionTests(TestCase):
 def setUp(self):
  NativeUploadHTTPTests.setUp(self)
  from django.test import override_settings
  settings=override_settings(CPJ_ARCHIVE_LIMITS={'upload_bytes':32*1024**2})
  settings.enable();self.addCleanup(settings.disable)
 upload_file=NativeUploadHTTPTests.upload_file
 def store(self,data):
  from cpjudge.imports import upload
  return upload(self.users['C5A'],self.upload_file(data),self.contests['c5a'])

 def test_supported_stored_package_extracts_without_conversion_or_execution(self):
  import os,subprocess
  from pathlib import Path
  from cpjudge.imports import extracted_upload,private_root
  data=Path('/tmp/cpj-tokens.zip').read_bytes();job=self.store(data)
  root=private_root();other=root/'other-job';other.mkdir();(other/'keep').write_text('preserve')
  with patch.dict(os.environ,{'PCC_ROOT':'/tmp/cpj-pcc'}),patch('compat.convert.convert',side_effect=AssertionError('No conversion')),patch('subprocess.check_output',wraps=subprocess.check_output) as calls:
   with extracted_upload(self.users['C5A'],job.pk) as (staging,findings):
    self.assertEqual((staging/'problem.xml').is_file(),True)
    self.assertEqual(findings['checker_executor'],'CPP17')
    self.assertEqual(staging.parent.stat().st_mode & 0o777,0o700)
   self.assertFalse(staging.exists())
   self.assertTrue(all(c.args[0][0]=='git' for c in calls.call_args_list))
  self.assertEqual((root/job.archive_key).read_bytes(),data)
  self.assertEqual((other/'keep').read_text(),'preserve')
  job.refresh_from_db();self.assertEqual((job.status,job.attempt),('uploaded',0))

 def test_service_rejection_cleanup_and_safe_errors(self):
  import io,zipfile,stat,os
  from pathlib import Path
  from cpjudge.imports import extracted_upload,private_root
  def archive(entries,compression=zipfile.ZIP_STORED):
   buffer=io.BytesIO()
   with zipfile.ZipFile(buffer,'w',compression=compression) as z:
    for name,value in entries:z.writestr(name,value)
   return buffer.getvalue()
  link=zipfile.ZipInfo('link');link.external_attr=(stat.S_IFLNK|0o777)<<16
  cases=[archive([(p,b'x')]) for p in ('../escape','/absolute')]
  cases += [archive([(link,b'target')]),archive([('A/x','1'),('a/y','2')]),archive([('é','1'),('e\u0301','2')]),archive([('x','1'),('x','2')]),archive([('x','1')],zipfile.ZIP_BZIP2)]
  # Supported ZIP with unsupported interactive Polygon policy.
  source=Path('/tmp/cpj-tokens.zip')
  with zipfile.ZipFile(source) as z:
   cases.append(archive([(n,z.read(n).replace(b'<judging',b'<interactor/><judging') if n=='problem.xml' else z.read(n)) for n in z.namelist()]))
  root=private_root();sentinel=root/'other-job';sentinel.mkdir();(sentinel/'keep').write_text('keep')
  for data in cases:
   job=self.store(data)
   with patch.dict(os.environ,{'PCC_ROOT':'/tmp/cpj-pcc'}),self.assertRaises(ValidationError) as caught:
    with extracted_upload(self.users['C5A'],job.pk):self.fail('Unsafe package accepted')
   self.assertNotIn(str(root),str(caught.exception))
   self.assertEqual((root/job.archive_key).read_bytes(),data)
   self.assertFalse(list(root.glob('extract-*')))
   self.assertEqual((sentinel/'keep').read_text(),'keep')

 def test_actual_extraction_limits_and_authorization_preserve_original(self):
  import io,zipfile
  from cpjudge.imports import extracted_upload,private_root
  buffer=io.BytesIO()
  with zipfile.ZipFile(buffer,'w') as z:z.writestr('first','x');z.writestr('second','x')
  job=self.store(buffer.getvalue());root=private_root()
  for config in ({'entries':1},{'expanded_bytes':1},{'member_bytes':1}):
   with self.settings(CPJ_ARCHIVE_LIMITS=config),patch.object(zipfile.ZipFile,'open',return_value=io.BytesIO(b'X'*100)),self.assertRaises(ValidationError):
    with extracted_upload(self.users['C5A'],job.pk):self.fail('Limit bypass')
   self.assertFalse(list(root.glob('extract-*')))
  from django.http import Http404
  with self.assertRaises(Http404):
   with extracted_upload(self.users['C5B'],job.pk):self.fail('Owner bypass')
  self.assertTrue((root/job.archive_key).is_file())
