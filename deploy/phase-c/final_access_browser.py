import json
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';root=Path('/results')
f=json.loads((root/'accounts.json').read_text());s=json.loads((root/'private-smoke.json').read_text())
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for role in ('a','b','p','q','admin'):
  account=f['accounts'][role];c=browser.new_context();page=c.new_page()
  c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(BASE+'/') else r.abort())
  page.goto(BASE+'/accounts/login/');page.locator('#id_username').fill(account.get('college_id',account['username']));page.locator('#id_password').fill(account['password'])
  page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/')
  permitted=role in ('a','p')
  for path in ('/src/'+str(s['id'])+'/raw','/submission/'+str(s['id']),'/cpjudge/events/sub_'+s['secret']):
   response=c.request.get(BASE+path)
   assert response.status==(200 if permitted else 404),(role,path,response.status)
  for path in ('/problem/pv000000000000000001/data/init.yml','/problem/pv000000000000000001/test_data','/tasks/ajax_status?id=known-id','/api/v2/submissions'):
   assert c.request.get(BASE+path).status==404
  if role=='b':
   response=c.request.get(BASE+'/contest/c1liveb/roster')
   assert response.status==200 and 'C1LIVECORRECTED' in response.text()
  c.close()
 browser.close()
(root/'final-access-browser.json').write_text(json.dumps({'status':'PASS','actual_submission_id':s['id'],'checks':['real submission source/result/channel owner and explicit reviewer access','other author, participant and account-admin denials with known object/channel IDs','native hidden files/global task/API routes fail closed','corrected canonical college ID displayed in scoped roster']},indent=2)+'\n')
print('Live final source/result/channel and private-route access matrix passed.')
