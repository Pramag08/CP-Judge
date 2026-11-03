import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path('/results');BASE='http://127.0.0.1:8000'
f=json.loads((ROOT/'accounts.json').read_text());accounts=f['accounts'];temporary=json.loads((ROOT/'recovery.json').read_text())
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 old=browser.new_context(storage_state=ROOT/'participant-session.json')
 assert old.request.get(BASE+'/edit/profile/').status==401
 assert old.request.get(BASE+'/cpjudge/events/submissions').status==401
 c=browser.new_context();page=c.new_page()
 c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
 page.goto(BASE+'/accounts/login/');page.locator('#id_username').fill(temporary['username']);page.locator('#id_password').fill(temporary['password'])
 page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/accounts/password/change/')
 new='Recovered-proof-password-837!'
 page.locator('[name=old_password]').fill(temporary['password']);page.locator('[name=new_password1]').fill(new);page.locator('[name=new_password2]').fill(new)
 page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/accounts/password/change/done/')
 assert c.request.get(BASE+'/edit/profile/').status==200
 accounts['p']['password']=new
 q=browser.new_context();qp=q.new_page();qp.goto(BASE+'/accounts/login/')
 qp.locator('#id_username').fill(accounts['q']['username']);qp.locator('#id_password').fill(accounts['q']['password'])
 qp.locator('form.form-area button[type=submit]').click()
 assert qp.locator('#form-errors').count()==1
 qp.locator('#id_username').fill('C1LIVECORRECTED');qp.locator('#id_password').fill(accounts['q']['password'])
 qp.locator('form.form-area button[type=submit]').click();qp.wait_for_url('**/contests/')
 accounts['q']['college_id']='C1LIVECORRECTED'
 (ROOT/'accounts.json').write_text(json.dumps(f))
 browser.close()
(ROOT/'recovery-browser.json').write_text(json.dumps({'status':'PASS','checks':['local organizer command recovery','reset revokes existing request and channel sessions','reset forces a strong password change','audited college ID correction retires old login and accepts corrected ID with unchanged password']},indent=2)+'\n')
print('Live organizer recovery, session revocation and college-ID correction passed.')
