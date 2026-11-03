"""One actual C10 private publication through the native author UI; no submissions."""
import json,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';OUT=Path('/results');JOB=24
accounts=json.loads(Path('/run/accounts.json').read_text())['accounts']
result={'status':'PASS','source_job':JOB,'checks':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 def login(role):
  c=b.new_context(viewport={'width':1440,'height':1000});attempts=[]
  c.on('request',lambda r:attempts.append(r.url))
  c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
  page=c.new_page();a=accounts[role];page.goto(BASE+'/accounts/login/')
  page.locator('#id_username').fill(a['username']);page.locator('#id_password').fill(a['password']);page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/')
  return c,page,attempts
 c,page,attempts=login('a');page.goto(BASE+f'/imports/{JOB}/');assert page.locator('#import-status').inner_text()=='succeeded'
 attempt=page.locator('#import-attempt').inner_text();assert attempt=='2'
 if not page.locator('#published-version').count():
  assert page.locator('#publish-form').count()==1
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('#publish-form button').click()
 assert page.locator('#publication-state').inner_text()=='published'
 code=page.locator('#published-version').inner_text();assert re.fullmatch('pv9[0-9]{17}',code);result['native_code']=code
 csrf=c.cookies(BASE);csrf=next(x['value'] for x in csrf if x['name']=='csrftoken')
 duplicate=c.request.post(BASE+f'/imports/{JOB}/publish/',form={'attempt':attempt,'csrfmiddlewaretoken':csrf})
 assert duplicate.status==200 and duplicate.url.endswith(f'/imports/{JOB}/')
 page.reload();assert page.locator('#published-version').inner_text()==code
 page.locator('#published-version').click();page.wait_for_load_state('networkidle')
 assert page.locator('#statement-preview').count()==1
 assert page.locator('#statement-preview img').evaluate('(e)=>e.complete && e.naturalWidth>0')
 assert page.locator('.statement-notice').count()>0
 page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise');page.evaluate('MathJax.startup.promise')
 assert page.locator('#statement-preview mjx-container').count()==1 and page.locator('mjx-merror').count()==0
 assert page.evaluate('window.c09Injected') is None
 assert not [u for u in attempts if 'c09-evil.invalid' in u]
 assert page.locator('#statement-preview script,#statement-preview iframe,#statement-preview [onclick],#statement-preview [onload]').count()==0
 assert page.locator('nav').count()>0 and page.locator('footer').count()>0
 image=page.locator('#statement-preview img').get_attribute('src')
 assert image.startswith('/problem/'+code+'/published-assets/')
 for path,kind in ((image,'image/png'),(f'/problem/{code}/published-assets/statement.css','text/css')):
  r=c.request.get(BASE+path);assert r.status==200 and r.headers['content-type'].startswith(kind)
  assert r.headers['cache-control']=='private, no-store' and r.headers['x-content-type-options']=='nosniff'
 result['checks']['native_statement_local_math_approved_image_notices_layout']=True
 result['checks']['duplicate_post_refresh_same_native_code']=True
 assert c.request.get(BASE+'/problem/pv900000000000000001').status==200
 result['checks']['earlier_c10_version_remains_usable']=True
 for method in ('get','post'):
  r=getattr(c.request,method)(BASE+f'/problem/{code}/submit',**({'form':{'csrfmiddlewaretoken':csrf}} if method=='post' else {}))
  assert r.status==403 and 'Worker readiness and judging probes' in r.text()
 for name in ('data.zip','checker.cpp','init.yml','raw.zip','statement.html','../data.zip','%2e%2e%2fdata.zip'):
  assert c.request.get(BASE+f'/problem/{code}/published-assets/'+name).status in (400,403,404)
 result['checks']['submission_admission_and_hidden_data_denied']=True
 for role in ('b','p',None):
  if role:other,view,_=login(role)
  else:other=b.new_context();view=other.new_page()
  for path in (f'/imports/{JOB}/',f'/problem/{code}',image):
   assert view.goto(BASE+path).status in (401,403,404)
  token=next((x['value'] for x in other.cookies(BASE) if x['name']=='csrftoken'),'missing')
  r=other.request.post(BASE+f'/imports/{JOB}/publish/',form={'attempt':attempt,'csrfmiddlewaretoken':token})
  assert r.status in (401,403,404)
  other.close()
 result['checks']['logged_out_participant_unrelated_author_denied']=True
 page.goto(BASE+f'/problem/{code}');page.wait_for_load_state('networkidle');page.screenshot(path=str(OUT/'published.png'),full_page=True)
 (OUT/'browser.json').write_text(json.dumps(result,indent=2)+'\n')
 c.close();b.close()
print('PASS: one actual private browser publication, duplicate/access/assets/submission-admission checks; no judging.')
