"""Actual Chromium C08 checks. No package text, credentials or raw HTML in reports."""
import io,json,re,time,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';OUT=Path('/results')
accounts=json.loads(Path('/run/accounts.json').read_text())['accounts']
attack='<img src=x onerror="window.c08Injected=1"><script>window.c08Injected=1</script>'
results={'status':'PASS','existing_success_job_id':13,'checks':{}}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 def login(role):
  c=browser.new_context();c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
  page=c.new_page();a=accounts[role];page.goto(BASE+'/accounts/login/')
  page.locator('#id_username').fill(a['username']);page.locator('#id_password').fill(a['password']);page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/')
  return c,page
 author,page=login('a')
 def snapshot():
  return {key:page.locator('#'+selector).inner_text() for key,selector in (
   ('name','problem-name'),('tests','test-count'),('samples','sample-count'),('time','time-limit'),('memory','memory-limit'),('standard','checker-standard'),('sha256','package-sha256'))}
 page.goto(BASE+'/imports/13/');assert page.locator('#compatibility-preview').count()==1
 original=snapshot();page.reload();assert snapshot()==original
 results['existing_success_display']=original
 results['checks']['existing_actual_conversion_refresh']=True
 def upload(mode):
  buffer=io.BytesIO()
  with zipfile.ZipFile('/run/groups.zip' if mode=='groups' else '/run/package.zip') as src,zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as dst:
   for info in src.infolist():
    data=src.read(info.filename)
    if info.filename=='problem.xml' and mode!='groups':
     if mode=='unsupported':data=data.replace(b'<judging',b'<interactor/><judging')
     else:
      name=escape(attack,{'"':'&quot;'})
      data=re.sub(rb'(<name\b[^>]*\bvalue=")[^"]*',lambda m:m.group(1)+name.encode(),data,count=1)
    dst.writestr(info,data)
   dst.comment=('C08-'+mode+'-1').encode()
  page.goto(BASE+'/contest/c1livea/import/')
  page.locator('input[name=package]').set_input_files({'name':'c08-'+mode+'.zip','mimeType':'application/zip','buffer':buffer.getvalue()})
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form[enctype="multipart/form-data"] button[type=submit]').click()
  match=re.fullmatch(r'/imports/(\d+)/',urlsplit(page.url).path);assert match
  return int(match.group(1))
 for mode in ('malicious-name','unsupported','groups'):
  job_id=upload(mode);results[mode+'_job_id']=job_id
  state=page.locator('#import-status').inner_text().strip()
  if state=='uploaded':
   assert page.locator('#compatibility-preview').count()==0
   with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form[action$="/convert/"] button').click()
  observed=[]
  for _ in range(300):
   state=page.locator('#import-status').inner_text().strip();observed.append(state)
   if state in ('succeeded','failed'):break
   assert page.locator('#compatibility-preview').count()==0
   page.wait_for_timeout(300);page.reload()
  assert state==('failed' if mode=='unsupported' else 'succeeded'),(mode,state)
  if mode=='unsupported':
   error=page.locator('#import-error').inner_text()
   assert 'Interactive problems are unsupported' in error and 'batch version' in error
   assert page.locator('#compatibility-preview').count()==0
   assert not any(x in error for x in ('/app/','/tmp/','<script>'))
   results['checks']['specific_actionable_unsupported_error']=True
  else:
   if mode=='malicious-name':assert page.locator('#problem-name').inner_text()==attack
   assert page.locator('#problem-name img, #problem-name script').count()==0
   assert page.evaluate('window.c08Injected') is None
   display=snapshot();page.reload();assert snapshot()==display
   if mode=='groups':
    rows=page.locator('#scoring-groups tr').all_inner_texts()
    assert len(rows)==4
    assert [re.split(r'\s+',r.strip()) for r in rows[1:]]==[['1','1','30.0','None'],['2','1','50.0','1'],['3','1','20.0','None']],rows
    results['checks']['actual_group_points_dependencies_displayed']=True
   assert page.evaluate('window.c08Injected') is None
   # Keep attacker-controlled name in private output only.
   results[mode+'_success_display']={k:v for k,v in display.items() if k!='name'}
   results['checks'][mode+'_success_inert_after_refresh']=True
  for _ in range(2):
   page.reload();assert page.locator('#import-status').inner_text().strip()==state
  results[mode+'_observed_states']=sorted(set(observed))
  for role in ('b','p'):
   c,other=login(role);response=other.goto(BASE+f'/imports/{job_id}/')
   assert response.status in (403,404)
   assert other.locator('#compatibility-preview').count()==0
   c.close()
  assert 'Judging verified: No' in page.locator('#judging-status').inner_text()
  assert 'Not ready for publication' in page.locator('#content-body').inner_text()
 results['checks']['participants_unrelated_authors_denied']=True
 results['checks']['pending_failed_no_success_findings']=True
 results['checks']['conversion_judging_publication_distinct']=True
 # Constructed state fixtures specifically exercise stale findings and hostile error text.
 receipt=json.loads(Path('/results/state-fixtures.json').read_text())
 for state,job_id in receipt.items():
  page.goto(BASE+f'/imports/{job_id}/')
  assert page.locator('#import-status').inner_text().strip()==state
  assert page.locator('#compatibility-preview').count()==0
  assert page.locator('#problem-name').count()==0
  assert page.locator('#import-error script, #import-error img').count()==0
  assert page.evaluate('window.c08Injected') is None
  if state=='failed':
   assert '/private/' not in page.locator('#import-error').inner_text()
   assert '<script>' not in page.locator('#import-error').inner_text()
 results['checks']['constructed_stale_findings_suppressed_in_browser']=True
 results['checks']['malicious_error_text_suppressed_in_browser']=True
 author.close();browser.close()
(OUT/'browser.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: C08 actual conversion/refresh/compatibility/isolation/escaping browser checks.')
