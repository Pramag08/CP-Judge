"""C09 actual retry/refresh plus deliberately stale queued/running fixtures."""
import json,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';OUT=Path('/results');data=json.loads((OUT/'fixtures.json').read_text())
accounts=json.loads(Path('/run/accounts.json').read_text())['accounts']
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);c=b.new_context()
 c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
 page=c.new_page();a=accounts['a'];page.goto(BASE+'/accounts/login/');page.locator('#id_username').fill(a['username']);page.locator('#id_password').fill(a['password']);page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/')
 job=data['retry_job'];old_asset=data['old_asset']
 for state,pk in data['states'].items():
  for _ in range(2):
   page.goto(BASE+f'/imports/{pk}/statement/');assert page.locator('#statement-preview').count()==0
   assert 'Statement preview unavailable' in page.locator('.statement-notice').inner_text()
  assert c.request.get(BASE+old_asset.replace(f'/imports/{job}/',f'/imports/{pk}/')).status==404
 page.goto(BASE+f'/imports/{job}/statement/');assert page.locator('#statement-preview').count()==0
 assert c.request.get(BASE+old_asset).status==404
 page.goto(BASE+f'/imports/{job}/');assert page.locator('#import-status').inner_text()=='failed'
 with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form[action$="/convert/"] button').click()
 states=[]
 for _ in range(300):
  state=page.locator('#import-status').inner_text();states.append(state)
  if state in ('failed','succeeded'):break
  assert page.locator('#statement-preview-link').count()==0
  page.wait_for_timeout(250);page.reload()
 assert state=='succeeded';assert page.locator('#import-attempt').inner_text()=='2'
 page.locator('#statement-preview-link').click()
 for _ in range(2):
  page.wait_for_load_state('networkidle');assert page.locator('#statement-attempt').inner_text()=='2'
  assert page.locator('#statement-preview img').evaluate('(e)=>e.complete && e.naturalWidth>0')
  asset=page.locator('#statement-preview img').get_attribute('src');assert '/statement/2/assets/' in asset
  assert c.request.get(BASE+asset).status==200;assert c.request.get(BASE+old_asset).status==404
  page.reload()
 assert page.evaluate('window.c09Injected') is None
 (OUT/'states.json').write_text(json.dumps({'status':'PASS','retry_job':job,'correct_current_successful_attempt':2,'observed_actual_retry_states':sorted(set(states)),'old_asset_denied':True,'constructed_stale_states_denied_on_refresh':list(data['states'])},indent=2)+'\n')
 c.close();b.close()
print('PASS: actual C09 retry advances to attempt2, old assets denied; constructed stale pending/failed previews denied.')
