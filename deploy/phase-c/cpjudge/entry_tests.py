"""Relevant DB/HTTP/race acceptance. Constructed results are not actual judging."""
import threading,uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
from django.db import close_old_connections,connection,transaction
from django.test import Client
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from judge.models import Contest,ContestParticipation,Submission,ContestSubmission
from cpjudge import entries as e
from cpjudge.models import ContestWorkflow,ContestProblemLabel,ContestEntry,ContestReceipt,Identity,Audit,Conflict
from cpjudge.integrated_tests import AdmissionTests
from cpjudge.policy import grant_scope
from cpjudge.native import contest_access,problem_access,visible_submissions
from cpjudge.admission import validate_execution

class EntryTests(AdmissionTests):
 def setUp(self):
  super().setUp()
  ContestWorkflow.objects.create(contest=self.contest,owner=self.users['C5A'])
  ContestProblemLabel.objects.create(contest_problem=self.cp,label='A')
  for u in self.users.values():
   if not u.email:
    u.email=u.username.lower()+'@private.invalid';u.save(update_fields=['email'])
   Identity.objects.filter(user=u).update(canonical_email=u.email.lower())
  for cap in ('settings.edit','roster.read','entrants.manage','submissions.review','source.review'):
   grant_scope(self.admin,self.users['C5A'],self.contest,cap)
  self.release()
  self.p=self.users['C5P'];self.q=self.users['C5B'];self.owner=self.users['C5A']
  self.before=self.contest.start_time-timedelta(seconds=1);self.running=self.contest.start_time+timedelta(seconds=30)
  self.base='/contest/'+self.contest.key
 def submit(self,user=None,key=None,source='int main(){}'):
  user=user or self.p;identity=Identity.objects.get(user=user)
  return e.admit(user,self.contest.key,self.v.code,self.lang.pk,source,key or str(uuid.uuid4()),generation=identity.generation,auth_hash=user.get_session_auth_hash())
 def register(self,user=None):return e.register(user or self.p,self.contest.key)
 def threaded(self,func):
  close_old_connections()
  try:return func()
  finally:close_old_connections()
 def test_prestart_idempotent_registration_withdraw_and_reregister(self):
  with patch('cpjudge.entries.server_now',return_value=self.before):
   entry=self.register();again=self.register();self.assertEqual(entry.pk,again.pk)
   self.assertEqual(ContestEntry.objects.count(),1);self.assertEqual(ContestParticipation.objects.filter(contest=self.contest).count(),1)
   self.assertEqual(Audit.objects.filter(action='entry.register').count(),1)
   e.deregister(self.p,self.contest.key);e.deregister(self.p,self.contest.key)
   self.assertEqual(Audit.objects.filter(action='entry.withdraw').count(),1)
   restored=self.register();self.assertEqual(entry.participation_id,restored.participation_id)
   self.assertFalse(e.content(self.p,self.contest));self.assertFalse(problem_access(self.p,self.v.problem))
   self.assertEqual(Contest.objects.get(pk=self.contest.pk).user_count,1)
 def test_late_entry_common_clock_boundaries_and_no_deregistration(self):
  for instant in (self.contest.start_time,self.contest.end_time-timedelta(microseconds=1)):
   with patch('cpjudge.entries.server_now',return_value=instant):
    entry=self.register();self.assertEqual(entry.participation.start,self.contest.start_time)
    self.assertEqual(entry.participation.end_time,self.contest.end_time)
    with self.assertRaises(PermissionDenied):e.deregister(self.p,self.contest.key)
  with patch('cpjudge.entries.server_now',return_value=self.contest.end_time):
   with self.assertRaises(PermissionDenied):self.register()
   with self.assertRaises(PermissionDenied):e.deregister(self.p,self.contest.key)
   with self.assertRaises(PermissionDenied):self.submit()
  Contest.objects.filter(pk=self.contest.pk).update(is_visible=False)
  with patch('cpjudge.entries.server_now',return_value=self.before),self.assertRaises(PermissionDenied):self.register()
 def test_parallel_registration_and_withdraw_are_single_entries(self):
  for action in ('register','withdraw'):
   barrier=threading.Barrier(2)
   def work():
    barrier.wait()
    return self.register().pk if action=='register' else e.deregister(self.p,self.contest.key).pk
   with patch('cpjudge.entries.server_now',return_value=self.before),ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(lambda _:self.threaded(work),range(2)))
   self.assertEqual(results[0],results[1])
  self.assertEqual(ContestEntry.objects.count(),1)
  self.assertEqual(Audit.objects.filter(action='entry.register').count(),1)
  self.assertEqual(Audit.objects.filter(action='entry.withdraw').count(),1)
 def test_boundary_time_is_sampled_after_contest_lock(self):
  # The request is at the SQL lock before the clock advances to the boundary.
  for operation,boundary in (('register',self.contest.end_time),('withdraw',self.contest.start_time),('submit',self.contest.end_time)):
   if operation in ('withdraw','submit'):
    with patch('cpjudge.entries.server_now',return_value=self.before):self.register()
   reached=threading.Event();now=[self.before]
   def observe(execute,sql,params,many,context):
    if 'judge_contest`' in sql and 'FOR UPDATE' in sql:reached.set()
    return execute(sql,params,many,context)
   def worker():
    with connection.execute_wrapper(observe):
     try:
      if operation=='register':self.register()
      elif operation=='withdraw':e.deregister(self.p,self.contest.key)
      else:self.submit()
     except PermissionDenied:return 'denied'
     return 'accepted'
   with patch('cpjudge.entries.server_now',side_effect=lambda:now[0]),ThreadPoolExecutor(max_workers=1) as pool:
    with transaction.atomic():
     Contest.objects.select_for_update().get(pk=self.contest.pk)
     future=pool.submit(self.threaded,worker)
     self.assertTrue(reached.wait(5));now[0]=boundary
    self.assertEqual(future.result(timeout=10),'denied')
 def test_submission_receipts_retry_end_and_concurrent_duplicate(self):
  with patch('cpjudge.entries.server_now',return_value=self.running),patch('cpjudge.entries.dispatch') as dispatch:
   self.register();key=str(uuid.uuid4());barrier=threading.Barrier(2)
   def work():barrier.wait();return self.submit(key=key)[0].pk
   with ThreadPoolExecutor(max_workers=2) as pool:ids=list(pool.map(lambda _:self.threaded(work),range(2)))
   self.assertEqual(ids[0],ids[1]);dispatch.assert_called_once();s=Submission.objects.get(pk=ids[0]);self.assertEqual(validate_execution(s).pk,ContestReceipt.objects.get(submission=s).approval_id)
   self.assertEqual(s.date,self.running)
  with patch('cpjudge.entries.server_now',return_value=self.contest.end_time):
   self.assertEqual(self.submit(key=key)[0].pk,s.pk)
   with self.assertRaises(PermissionDenied):self.submit()
   with self.assertRaises(PermissionDenied):self.submit(key=key,source='different source')
  self.assertEqual(ContestReceipt.objects.count(),1)
 def test_racing_removal_and_submission_has_no_post_removal_admission(self):
  with patch('cpjudge.entries.server_now',return_value=self.running),patch('cpjudge.entries.dispatch'):
   entry=self.register();barrier=threading.Barrier(2)
   def submit():
    barrier.wait()
    try:return self.submit()[0].pk
    except PermissionDenied:return None
   def remove():barrier.wait();e.sanction(self.owner,self.contest.key,entry.pk,'remove','Race acceptance');return 'removed'
   with ThreadPoolExecutor(max_workers=2) as pool:
    f=pool.submit(self.threaded,submit);g=pool.submit(self.threaded,remove);sid=f.result(timeout=15);self.assertEqual(g.result(timeout=15),'removed')
   self.assertEqual(ContestEntry.objects.get(pk=entry.pk).status,'removed')
   if sid:self.assertTrue(validate_execution(Submission.objects.get(pk=sid)))
   count=ContestReceipt.objects.count()
   with self.assertRaises(PermissionDenied):self.submit()
   self.assertEqual(ContestReceipt.objects.count(),count)
 def test_http_csrf_cross_scope_roster_privacy_poll_and_native_bypasses(self):
  participant=self.logged('C5P');other=self.logged('C5B');author=self.logged('C5A')
  csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.p,backend='cpjudge.identity.CollegeBackend')
  self.assertEqual(csrf.post(self.base+'/register').status_code,403)
  participant=self.logged('C5P')
  for suffix in ('/register','/deregister','/join','/leave'):
   self.assertEqual(participant.get(self.base+suffix).status_code,405)
  with patch('cpjudge.entries.server_now',return_value=self.before):
   self.assertEqual(participant.post(self.base+'/join',{'virtual':1}).status_code,302)
   entry=ContestEntry.objects.get(user=self.p)
   self.assertEqual(entry.participation.virtual,0)
   for client in (participant,other):
    self.assertIn(client.get(self.base+'/roster').status_code,(403,404))
    self.assertIn(client.post(self.base+f'/entries/{entry.pk}/sanction',{'action':'remove','reason':'not authorized'}).status_code,(403,404))
   response=author.get(self.base+'/roster');self.assertEqual(response.status_code,200);self.assertIn(self.p.email,response.content.decode())
   self.assertEqual(author.post(self.base+'/roster/export').status_code,404)
   self.assertIn(author.post(self.base+f'/entries/{entry.pk}/sanction',{'action':'dq','reason':' '}).status_code,(400,403))
   # An entry ID from this contest cannot be targeted through another contest URL.
   self.assertIn(author.post('/contest/c5a/entries/'+str(entry.pk)+'/sanction',{'action':'dq','reason':'wrong scope'}).status_code,(403,404))
  with patch('cpjudge.entries.server_now',return_value=self.running),patch('cpjudge.entries.dispatch'):
   s,_=self.submit()
   self.assertEqual(participant.post('/problem/'+self.v.code+'/submit',{'language':self.lang.pk,'source':'int main(){}'}).status_code,403)
   self.assertEqual(participant.post(self.base+'/leave').status_code,302)
   self.assertEqual(ContestEntry.objects.get(pk=entry.pk).status,'active')
   self.assertEqual(participant.get(self.base+'/problem/'+self.v.code+'/submit').status_code,200)
   self.assertEqual(participant.post(self.base+'/deregister').status_code,403)
   self.assertEqual(author.post(self.base+f'/entries/{entry.pk}/sanction',{'action':'remove','reason':'Browser style removal'}).status_code,302)
   for path in (self.base,self.base+'/join',self.base+'/register','/problem/'+self.v.code,'/problem/'+self.v.code+'/published-assets/statement.css',self.base+'/problem/'+self.v.code+'/submit','/submission/'+str(s.pk),'/src/'+str(s.pk)+'/raw','/widgets/submission_testcases?id='+str(s.pk),'/cpjudge/events/sub_'+s.id_secret,'/cpjudge/events/contest_'+str(self.contest.pk)):
    self.assertIn(participant.get(path).status_code,(403,404,405),path)
   self.assertIn(participant.post(self.base+'/join').status_code,(403,404))
   self.assertNotIn(s.pk,[r['id'] for r in participant.get('/cpjudge/events/submissions').json()['messages']])
   self.assertTrue(author.get('/submission/'+str(s.pk)).status_code==200)
   self.assertFalse(visible_submissions(self.p,Submission.objects.all()).filter(pk=s.pk).exists())
   self.assertEqual(other.get('/contest/c5b').status_code,200)
 def test_conflicts_and_session_are_checked_under_admission_lock(self):
  with patch('cpjudge.entries.server_now',return_value=self.running),patch('cpjudge.entries.dispatch'):
   with self.assertRaises(PermissionDenied):self.register(self.owner)
   entry=self.register()
   identity=Identity.objects.get(user=self.p)
   with self.assertRaises(PermissionDenied):e.admit(self.p,self.contest.key,self.v.code,self.lang.pk,'int main(){}',str(uuid.uuid4()),generation=identity.generation+1,auth_hash=self.p.get_session_auth_hash())
   grant_scope(self.admin,self.p,self.contest,'submissions.review')
   entry.participation.refresh_from_db();self.assertEqual(entry.participation.virtual,-1)
   grant_scope(self.admin,self.p,self.contest,'submissions.review',revoke=True)
   self.assertTrue(Conflict.objects.filter(user=self.p,contest=self.contest).exists())
   with self.assertRaises(PermissionDenied):self.submit()
   with self.assertRaises(PermissionDenied):self.register()
 def test_exact_start_receipt_and_stale_sanction_session(self):
  with patch('cpjudge.entries.server_now',return_value=self.contest.start_time),patch('cpjudge.entries.dispatch'):
   entry=self.register();s,_=self.submit();self.assertEqual(s.date,self.contest.start_time)
   i=Identity.objects.get(user=self.owner)
   with self.assertRaises(PermissionDenied):e.sanction(self.owner,self.contest.key,entry.pk,'remove','Stale session',generation=i.generation+1,auth_hash=self.owner.get_session_auth_hash())
   self.assertEqual(ContestEntry.objects.get(pk=entry.pk).status,'active')
   e.sanction(self.owner,self.contest.key,entry.pk,'remove','Authoritative access state')
   self.contest.banned_users.remove(self.p.profile)
   self.assertFalse(contest_access(self.p,self.contest))
   self.assertFalse(visible_submissions(self.p,Submission.objects.all()).filter(pk=s.pk).exists())
   with self.assertRaises(PermissionDenied):self.register()

 def test_removal_retains_score_dq_excludes_and_callbacks_preserve_evidence(self):
  with patch('cpjudge.entries.server_now',return_value=self.running),patch('cpjudge.entries.dispatch'):
   first=self.register();second=self.register(self.q)
   s,_=self.submit();t,_=self.submit(self.q)
   for item in (s,t):
    Submission.objects.filter(pk=item.pk).update(status='D',result='AC',case_points=3,case_total=3);item.refresh_from_db();item.update_contest()
   first.participation.refresh_from_db();before=(first.participation.score,first.participation.cumtime)
   self.assertEqual(before,(1,30))
   author=self.logged('C5A')
   e.sanction(self.owner,self.contest.key,first.pk,'remove','Retain score')
   self.assertTrue(validate_execution(s))
   response=author.get(self.base+'/ranking/');self.assertEqual(response.status_code,200);self.assertContains(response,'Removed')
   e.sanction(self.owner,self.contest.key,first.pk,'dq','Exclude rank')
   s.update_contest();first.participation.refresh_from_db();self.assertEqual((first.participation.score,first.participation.cumtime),before)
   response=author.get(self.base+'/ranking/');self.assertContains(response,'DQ');self.assertNotIn(self.p.email,response.content.decode())
   from judge.views.contests import get_contest_ranking_list
   request=__import__('types').SimpleNamespace(user=self.owner,profile=self.owner.profile)
   rows,_=get_contest_ranking_list(request,self.contest,show_current_virtual=False)
   self.assertEqual([(rank,row.participation.pk) for rank,row in rows],[(1,second.participation_id)])
   self.assertEqual(ContestSubmission.objects.filter(submission__in=[s,t]).count(),2)
   self.assertEqual(Audit.objects.filter(action='entry.dq',subject=self.p).get().details['reason'],'Exclude rank')

# Reuse fixtures; accepted Phase C suites are not repeated.
for _name in dir(AdmissionTests):
 if _name.startswith('test_'):setattr(EntryTests,_name,None)
