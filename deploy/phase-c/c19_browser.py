"""Actual initial/reset email login, revocation and voluntary password change."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path('/results');BASE='http://127.0.0.1:8000';data=json.loads((ROOT/'new-account.json').read_text());out={'status':'PASS','checks':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 def login(email,password):
  c=b.new_context();page=c.new_page();page.goto(BASE+'/accounts/login/')
  page.locator('#id_username').fill(email);page.locator('#id_password').fill(password)
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form.form-area button[type=submit]').click()
  return c,page
 c,page=login(data['email'],data['password']);assert page.url.endswith('/contests/')
 assert page.goto(BASE+'/edit/profile/').status==200
 assert page.get_by_role('link',name='Change password (optional)').count()==1
 state=c.storage_state();c.storage_state(path=ROOT/'before-reset-state.json');clones=[b.new_context(storage_state=state) for _ in range(3)]
 (ROOT/'ready-reset').write_text('Synthetic fixture ready for verified organizer reset.\n')
 for _ in range(240):
  if (ROOT/'reset.json').exists():break
  time.sleep(.5)
 else:raise AssertionError('Reset controller did not complete')
 reset=json.loads((ROOT/'reset.json').read_text())
 assert clones[0].request.get(BASE+'/edit/profile/').status==401
 csrf=next(cookie['value'] for cookie in state['cookies'] if cookie['name']=='csrftoken')
 assert clones[1].request.post(BASE+'/edit/profile/',form={'first_name':'stale'},headers={'X-CSRFToken':csrf}).status==401
 assert clones[2].request.get(BASE+'/cpjudge/events/submissions').status==401
 wrong,wp=login(data['email'],data['password']);assert wp.locator('#form-errors').count()==1;wrong.close()
 fresh,fp=login(reset['email'],reset['password']);assert fp.url.endswith('/contests/')
 assert fp.goto(BASE+'/edit/profile/').status==200
 for path in ('/admin/auth/user/','/contest/c1livea/roster'):
  assert fp.goto(BASE+path).status in (403,404)
 replace,rp=login(reset['email'],reset['password']);assert rp.url.endswith('/contests/')
 assert fresh.request.get(BASE+'/cpjudge/events/submissions').status==401
 rp.goto(BASE+'/accounts/password/change/')
 voluntary='Voluntary-acceptance-password-349!'
 rp.locator('[name=old_password]').fill(reset['password']);rp.locator('[name=new_password1]').fill(voluntary);rp.locator('[name=new_password2]').fill(voluntary)
 with rp.expect_navigation(wait_until='domcontentloaded'):rp.locator('form button[type=submit],form input[type=submit]').last.click()
 assert rp.url.endswith('/accounts/password/change/done/')
 assert rp.goto(BASE+'/edit/profile/').status==200
 assert 'outside this application' in replace.request.get(BASE+'/accounts/password/reset/').text()
 out['checks']={'provisioned_external_without_college_id':True,'first_email_login_no_forced_change':True,'verified_organizer_reset':True,'stale_read_post_polling_rejected':True,'old_password_rejected':True,'reset_email_login_no_forced_change':True,'replacement_revocation':True,'optional_password_change':True,'recovery_contact_only':True,'role_privacy':True}
 rp.screenshot(path=ROOT/'optional-password-profile.png');b.close()
(ROOT/'result.json').write_text(json.dumps(out,indent=2)+'\n')
print('Initial/reset browser email login, stale-session revocation and voluntary change passed.')
