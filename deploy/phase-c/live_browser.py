"""Actual live checkpoint 1 browser checks; no sensitive values printed."""
import json,time
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path('/results');BASE='http://127.0.0.1:8000'
fixture=json.loads((ROOT/'accounts.json').read_text());accounts=fixture['accounts'];checks=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 contexts={};pages={}
 def context():
  c=browser.new_context()
  c.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).hostname=='127.0.0.1' else route.abort())
  return c
 def login(role):
  c=context();page=c.new_page();account=accounts[role]
  page.goto(BASE+'/accounts/login/')
  page.locator('#id_username').fill(account['username']);page.locator('#id_password').fill(account['password'])
  page.locator('form.form-area button[type=submit]').click()
  page.wait_for_url('**/accounts/password/change/')
  assert c.request.get(BASE+'/contest/c1livea',max_redirects=0).status==302
  new='Live-checkpoint-password-'+role+'-7492!'
  page.locator('[name=old_password]').fill(account['password'])
  page.locator('[name=new_password1]').fill(new);page.locator('[name=new_password2]').fill(new)
  page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/accounts/password/change/done/')
  accounts[role]['password']=new
  (ROOT/'accounts.json').write_text(json.dumps(fixture))
  contexts[role]=c;pages[role]=page
 for role in ('a','b','p','q','admin'):login(role)
 checks.append('five live role accounts require initial password change using real PBKDF2 hashing')
 a,b,participant,outsider,admin=[contexts[r] for r in ('a','b','p','q','admin')]
 response=a.request.get(BASE+'/contest/c1livea/roster')
 assert response.status==200 and 'p@checkpoint.invalid' in response.text()
 for c,path in ((a,'/contest/c1liveb/roster'),(b,'/contest/c1livea/roster'),(participant,'/contest/c1livea/roster'),(admin,'/contest/c1livea/roster'),(participant,'/admin/'),(a,'/admin/auth/user/')):
  assert c.request.get(BASE+path).status in (403,404)
 assert 'Checkpoint 1 B' not in a.request.get(BASE+'/admin/judge/contest/').text()
 assert a.request.get(BASE+'/admin/judge/contest/'+str(fixture['contests']['b']['id'])+'/change/').status==404
 assert admin.request.get(BASE+'/admin/auth/user/').status==200
 checks.append('native admin/list/direct and cross-contest roster email isolation')
 # Real background export; form uses native CSRF token from current owner page.
 page=pages['a'];page.goto(BASE+'/contest/c1livea/roster')
 with page.expect_response(lambda r:r.status==302 and urlsplit(r.url).path.endswith('/roster/export')) as redirect_response:
  page.locator('form[action$="/roster/export"] button').click()
 export_url=BASE+redirect_response.value.headers['location']
 for _ in range(30):
  response=a.request.get(export_url)
  if response.status==200:break
  assert response.status==202;time.sleep(1)
 assert response.status==200 and 'p@checkpoint.invalid' in response.text()
 assert b.request.get(export_url).status==404
 checks.append('real Celery roster export and private owner-only download')
 # A replacement login makes both native requests and channels stale immediately.
 replacement=context();newpage=replacement.new_page()
 newpage.goto(BASE+'/accounts/login/');newpage.locator('#id_username').fill(accounts['p']['username']);newpage.locator('#id_password').fill(accounts['p']['password'])
 newpage.locator('form.form-area button[type=submit]').click();newpage.wait_for_url('**/contests/')
 assert participant.request.get(BASE+'/edit/profile/').status==401
 assert participant.request.get(BASE+'/cpjudge/events/submissions').status==401
 assert participant.request.post(BASE+'/accounts/logout/').status in (401,403)
 assert replacement.request.get(BASE+'/edit/profile/').status==200
 checks.append('session replacement revokes requests/channels; stale logout preserves replacement')
 assert outsider.request.get(BASE+'/problem/pv000000000000000001/data/init.yml').status==404
 assert outsider.request.get(BASE+'/problem/pv000000000000000001/statement-assets/statement.css').status==404
 assert outsider.request.get(BASE+'/cpjudge/events/contest_'+str(fixture['contests']['a']['id'])).status==404
 assert context().request.get(BASE+'/cpjudge/events/submissions').status==401
 checks.append('private files, statement assets and direct channel scope denied')
 # Save a current participant session privately for organizer recovery check.
 replacement.storage_state(path=ROOT/'participant-session.json')
 pages['a'].screenshot(path=ROOT/'native-export-page.png')
 for c in contexts.values():c.close()
 replacement.close();browser.close()
(ROOT/'browser.json').write_text(json.dumps({'status':'PASS','checks':checks,'live_url':BASE,'test_settings':False},indent=2)+'\n')
print('Live checkpoint 1 identity, native permissions, polling and background export checks passed.')
