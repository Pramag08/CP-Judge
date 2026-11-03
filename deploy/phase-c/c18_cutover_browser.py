"""Actual four-account email cutover, admin-route and generation checks."""
import json,sys
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path('/results');BASE='http://127.0.0.1:8000';rows=json.loads((ROOT/'accounts.json').read_text());phase=sys.argv[1]
result={'status':'PASS','phase':phase,'checks':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 def context(state=None):
  c=b.new_context(storage_state=state);c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort());return c
 def login(identifier,password,*,start='/accounts/login/'):
  c=context();page=c.new_page();page.goto(BASE+start)
  page.locator('#id_username').fill(identifier);page.locator('#id_password').fill(password)
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form.form-area button[type=submit]').click()
  return c,page
 def success(page):
  assert page.url.endswith(('/contests/','/admin/'))
  assert '/password/change' not in page.url
 if phase=='before':
  for row in rows[:2]:
   c,page=login(row['username'],row['password']);success(page)
   assert page.goto(BASE+'/edit/profile/').status==200
   c.storage_state(path=ROOT/f"before-{row['user_id']}.json")
   (ROOT/f"before-{row['user_id']}.json").chmod(0o600);c.close()
  result['checks']={'legacy_login_after_mapping_still_worked':True,'two_pre_cutover_sessions_saved_privately':True,'no_forced_change':True}
 elif phase=='admin-route':
  staff=rows[0];c=context();page=c.new_page();page.goto(BASE+'/admin/login/?next=/admin/')
  token=next(cookie['value'] for cookie in c.cookies() if cookie['name']=='csrftoken')
  response=c.request.post(BASE+'/admin/login/',form={'username':staff['username'],'password':staff['password'],'csrfmiddlewaretoken':token},max_redirects=0)
  assert response.status==302 and response.headers['location'].startswith('/accounts/login/')
  assert c.request.get(BASE+'/admin/').status==401
  result['checks']={'direct_native_admin_username_post_cannot_authenticate':True,'native_admin_redirects_to_email_form':True}
 elif phase=='after':
  # These are the actual successful pre-cutover browser sessions; passwords did
  # not change, so rejection proves generation revocation by policy cutover.
  old_admin=context(ROOT/'before-1.json');assert old_admin.request.get(BASE+'/admin/').status==401;old_admin.close()
  old_state=json.loads((ROOT/'before-2.json').read_text());token=next(c['value'] for c in old_state['cookies'] if c['name']=='csrftoken')
  for method,path in [('get','/edit/profile/'),('post','/edit/profile/'),('get','/cpjudge/events/submissions')]:
   old=context(ROOT/'before-2.json')
   kwargs={'form':{'first_name':'stale'},'headers':{'X-CSRFToken':token}} if method=='post' else {}
   assert getattr(old.request,method)(BASE+path,**kwargs).status==401;old.close()
  result['checks']['cutover_revokes_actual_old_read_write_poll_admin_sessions']=True
  active={}
  for row in rows:
   wrong,page=login(row['username'],row['password'])
   assert page.locator('#form-errors').count()==1 and urlsplit(page.url).path=='/accounts/login/'
   assert wrong.request.get(BASE+'/edit/profile/').status==401;wrong.close()
   identifier=' '+row['email'].upper()+' ' if row['user_id']==1 else row['email']
   c,page=login(identifier,row['password']);success(page)
   assert page.goto(BASE+'/edit/profile/').status==200
   assert page.get_by_role('link',name='Change password (optional)').count()==1
   if row['user_id']==1:
    assert page.goto(BASE+'/admin/auth/user/').status==200
   else:
    assert page.goto(BASE+'/admin/auth/user/').status in (403,404)
   if row.get('history_submission'):
    sid=row['history_submission']
    assert c.request.get(BASE+f'/submission/{sid}').status==200
    assert c.request.get(BASE+f'/widgets/submission_testcases?id={sid}').status==200
    assert c.request.get(BASE+f'/src/{sid}/raw').status==200
   active[row['user_id']]=(c,page)
  # Native admin login redirects to the same email form, with no legacy bypass.
  staff=rows[0]
  denied,page=login(staff['username'],staff['password'],start='/admin/login/?next=/admin/')
  assert page.locator('#form-errors').count()==1;assert denied.request.get(BASE+'/admin/').status==401;denied.close()
  admin,page=login(staff['email'],staff['password'],start='/admin/login/?next=/admin/')
  success(page);assert page.goto(BASE+'/admin/auth/user/').status==200
  bad,page=login(rows[1]['email'],'deliberately-wrong-password')
  assert page.locator('#form-errors').count()==1;bad.close()
  # A replacement login still invalidates the old generation; stale logout
  # cannot revoke the current replacement. No live password reset is used.
  original,page=active[2];state=original.storage_state();csrf=next(c['value'] for c in state['cookies'] if c['name']=='csrftoken')
  replacement,rp=login(rows[1]['email'],rows[1]['password']);success(rp)
  for method,path in [('get','/edit/profile/'),('post','/edit/profile/'),('get','/cpjudge/events/submissions'),('post','/accounts/logout/')]:
   stale=context(state)
   kwargs={'form':{'first_name':'stale'},'headers':{'X-CSRFToken':csrf}} if method=='post' else {}
   assert getattr(stale.request,method)(BASE+path,**kwargs).status==401;stale.close()
  assert replacement.request.get(BASE+'/edit/profile/').status==200
  assert replacement.request.get(BASE+'/accounts/password/change/').status==200
  assert 'outside this application' in replacement.request.get(BASE+'/accounts/password/reset/').text()
  profile=replacement.request.get(BASE+'/edit/profile/').text()
  assert all(row['email'] not in profile for row in rows if row['user_id']!=2)
  rp.goto(BASE+'/edit/profile/');rp.screenshot(path=ROOT/'email-only-profile.png')
  result['checks'].update(four_email_password_logins_existing_passwords=True,existing_submission_history_access=True,four_username_logins_rejected=True,admin_route_username_rejected_email_admin_access=True,no_forced_change_all_four=True,wrong_password_rejected=True,replacement_stale_read_write_poll_logout_rejected=True,replacement_session_survives_stale_logout=True,optional_change_available_not_performed=True,contact_only_recovery=True,other_email_privacy=True)
 else:raise AssertionError('Unknown browser phase')
 b.close()
(ROOT/('result-'+phase+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print('Actual '+phase+' email cutover browser checks passed; no password changes performed.')
