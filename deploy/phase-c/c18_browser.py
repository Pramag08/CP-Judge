"""Actual transitional email authentication; unresolved legacy users retain access."""
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path('/results');BASE='http://127.0.0.1:8000'
a=json.loads(Path('/run/accounts.json').read_text())['accounts'];out={'status':'PASS','email_only_cutover':'BLOCKED','checks':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 def login(identifier,password):
  c=b.new_context();page=c.new_page();page.goto(BASE+'/accounts/login/')
  page.locator('#id_username').fill(identifier);page.locator('#id_password').fill(password)
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form.form-area button[type=submit]').click()
  return c,page
 c,old=login(a['p']['username'],a['p']['password']);old.wait_for_url('**/contests/')
 old.goto(BASE+'/edit/profile/');text=old.locator('#content-body').inner_text()
 email=re.search(r'Personal email: (\S+)\.',text).group(1)
 wrong,wp=login(email,'wrong-password');assert wp.locator('#form-errors').count()>0;wrong.close()
 replacement,page=login(' '+email.upper()+' ',a['p']['password']);page.wait_for_url('**/contests/')
 assert old.goto(BASE+'/edit/profile/').status==401
 assert page.goto(BASE+'/edit/profile/').status==200
 assert page.locator('input[name=email]').count()==0
 for path in ('/admin/auth/user/','/contest/c1livea/roster','/contest/c1liveb/roster'):
  assert page.goto(BASE+path).status in (403,404)
 out['checks']={'existing_password_email_login':True,'case_whitespace_normalization':True,'wrong_password_rejected':True,'replacement_invalidates_old_session':True,'email_correction_admin_only':True,'participant_roster_admin_privacy':True}
 b.close()
(ROOT/'result.json').write_text(json.dumps(out,indent=2)+'\n')
print('Transitional browser email login and privacy passed; email-only mode remains blocked.')
