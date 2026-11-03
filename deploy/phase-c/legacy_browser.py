import json
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';account=json.loads(Path('/run/legacy.json').read_text())['participant']
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True);context=browser.new_context();page=context.new_page()
 context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(BASE+'/') else r.abort())
 page.goto(BASE+'/accounts/login/');page.locator('#id_username').fill(account['username']);page.locator('#id_password').fill(account['password'])
 page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/')
 assert context.request.get(BASE+'/edit/profile/').status==200
 page.goto(BASE+'/edit/profile/')
 assert 'Not assigned (legacy account)' in page.locator('#content-body').inner_text()
 browser.close()
Path('/results/legacy-browser.json').write_text(json.dumps({'status':'PASS','existing_legacy_password_works':True,'college_id_not_guessed':True},indent=2)+'\n')
print('Existing legacy account password works; no college ID guessed or password reset.')
