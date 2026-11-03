"""Reuse imported/probed exact version; actual official browser judging/standings."""
import json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';OUT=Path('/results');f=json.loads((OUT/'fixture.json').read_text())
a=json.loads(Path('/run/accounts.json').read_text())['accounts'];CODE=f['code'];KEY=f['contest'];receipts=OUT/'receipts.json'
runs=json.loads(receipts.read_text()) if receipts.exists() else []
result={'status':'PASS','version_id':f['version_id'],'code':CODE,'digest':f['digest'],'job_id':f['job_id'],'attempt':f['attempt'],'probe_id':f['probe_id'],'admission_id':f['admission_id'],'checks':{},'runs':runs}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 def login(role):
  c=b.new_context(viewport={'width':1440,'height':1000});c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
  page=c.new_page();page.on('dialog',lambda dialog:dialog.accept());page.goto(BASE+'/accounts/login/');page.locator('#id_username').fill(a[role].get('login',a[role]['username']));page.locator('#id_password').fill(a[role]['password'])
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form.form-area button[type=submit]').click()
  if not page.url.endswith('/contests/'):
   (OUT/'login-diagnostic.json').write_text(json.dumps({'role':role,'path':urlsplit(page.url).path,'form_errors':page.locator('#form-errors').count()}))
   raise AssertionError('Login did not reach contest list; inspect private diagnostic')
  return c,page
 author,ap=login('a');ap.goto(BASE+f"/imports/{f['job_id']}/")
 assert ap.locator('#publication-state').inner_text()=='published' and ap.locator('#published-version').inner_text()==CODE
 assert ap.locator('#import-attempt').inner_text()==str(f['attempt'])
 response=author.request.get(BASE+f"/imports/{f['job_id']}/download/");assert response.status==200
 import hashlib
 assert hashlib.sha256(response.body()).hexdigest()==f['package_sha256']
 # Re-upload through the actual author form; reuse C12 deduplication and preserve
 # the existing conversion/publication/probe rather than convert the same bytes.
 ap.goto(BASE+'/contest/c1livea/import/')
 ap.locator('input[name=package]').set_input_files({'name':'integrated-original.zip','mimeType':'application/zip','buffer':response.body()})
 with ap.expect_navigation(wait_until='domcontentloaded'):ap.locator('form[enctype="multipart/form-data"] button[type=submit]').click()
 assert urlsplit(ap.url).path==f"/imports/{f['job_id']}/" and ap.locator('#published-version').inner_text()==CODE
 ap.goto(BASE+f"/private-versions/{f['version_id']}/probes/")
 row=ap.locator(f'[data-probe="{f["probe_id"]}"]');assert row.locator('.probe-status').inner_text().strip()=='AC' and row.locator('td').last.inner_text()=='Yes'
 result['checks']['browser_upload_dedup_same_conversion_publication_probe_receipt']=True
 outsider,op=login('b')
 for path in (f'/contest/{KEY}',f'/contest/{KEY}/ranking',f'/problem/{CODE}',f'/problem/{CODE}/submit',f"/private-versions/{f['version_id']}/probes/"):
  assert op.goto(BASE+path).status in (403,404)
 outsider.close()
 contexts={}
 for role in ('p','q'):
  c,page=login(role);contexts[role]=(c,page)
  if datetime.now(timezone.utc)<datetime.fromisoformat(f['start']):assert c.request.get(BASE+'/problem/'+CODE+'/submit').status in (403,404)
 # Browser waits only for the server's published schedule; server admission is authoritative.
 for _ in range(240):
  if datetime.now(timezone.utc)>=datetime.fromisoformat(f['start']):break
  time.sleep(.25)
 else:raise AssertionError('Fixture start outside bounded wait')
 for role,(c,page) in contexts.items():
  page.goto(BASE+'/contest/'+KEY)
  join=page.locator(f'form[action="/contest/{KEY}/join"] input[type=submit]')
  if join.count():
   with page.expect_navigation(wait_until='domcontentloaded'):join.click()
  assert c.request.get(BASE+'/problem/'+CODE).status==200
  assert c.request.get(BASE+f"/private-versions/{f['version_id']}/probes/").status in (403,404)
  assert c.request.get(BASE+f"/imports/{f['job_id']}/download/").status in (403,404)
 result['checks']['unrelated_author_denied_and_participants_no_probe_package_access']=True
 def submit(role,name,wanted):
  c,page=contexts[role];existing=next((x for x in runs if x['name']==name),None)
  if existing:sid=existing['id'];page.goto(BASE+'/submission/'+str(sid))
  else:
   page.goto(BASE+'/problem/'+CODE+'/submit');page.wait_for_function("Boolean(window.ace_source)")
   page.locator('#id_language').select_option(value=str(f['runtime_id']),force=True)
   page.wait_for_function('window.jQuery.active===0')
   src=(OUT/('wrong.cpp' if wanted=='WA' else 'accepted.cpp')).read_text()
   page.evaluate('s=>window.ace_source.getSession().setValue(s)',src)
   assert page.locator('#id_source').input_value()==src
   with page.expect_navigation(wait_until='domcontentloaded',timeout=60000):page.locator('#problem_submit input[type=submit]').click()
   match=re.fullmatch(r'/submission/(\d+)/?',urlsplit(page.url).path);assert match,'No native admission receipt'
   sid=int(match.group(1));runs.append({'name':name,'role':role,'id':sid,'expected':wanted});receipts.write_text(json.dumps(runs,indent=2));receipts.chmod(0o600)
  page.wait_for_function("document.querySelectorAll('#test-cases .case-row').length===3 && document.querySelector('#test-cases').textContent.includes('Final score:')",timeout=120000)
  statuses=[x.strip() for x in page.locator('#test-cases .case-row td:nth-child(2) span').all_text_contents()]
  assert statuses==[wanted]*3
  page.screenshot(path=OUT/(name+'-cases.png'))
  for r in runs:
   if r['id']==sid:r['verdict']=wanted;r['cases']=3
  receipts.write_text(json.dumps(runs,indent=2));receipts.chmod(0o600)
 submit('p','p-wrong','WA');submit('p','p-accepted','AC');submit('q','q-accepted','AC')
 # Each participant can read their own results, never another's source.
 for owner,(c,page) in contexts.items():
  for run in runs:
   response=c.request.get(BASE+f"/src/{run['id']}/raw")
   assert response.status==(200 if owner==run['role'] else 404)
  page.goto(BASE+'/contest/'+KEY+'/ranking',wait_until='domcontentloaded')
  page.locator('#ranking-table').wait_for(timeout=15000)
  (OUT/(owner+'-standings.html')).write_text(page.content())
  page.screenshot(path=OUT/(owner+'-standings.png'))
  text=page.locator('#ranking-table').inner_text()
  assert a['p']['username'] in text and a['q']['username'] in text
  assert '@' not in page.locator('#ranking-table').inner_text()
 result['checks']['official_native_form_case_verdicts_and_private_sources']=True
 result['runs']=runs
 b.close()
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('Same-version author re-upload/probe and three official browser worker results completed; native standings displayed.')
