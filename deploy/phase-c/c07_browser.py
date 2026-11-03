"""C07 actual author upload/queue/refresh flow; no credentials in output."""
import io,json,os,re,time,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';OUT=Path('/results')
mode=os.environ.get('MODE','supported')
accounts=json.loads(Path('/run/accounts.json').read_text())['accounts']
blocked=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 def context():
  c=browser.new_context();c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else (blocked.append(urlsplit(r.request.url).hostname),r.abort())[1]);return c
 def login(role):
  c=context();page=c.new_page();account=accounts[role]
  page.goto(BASE+'/accounts/login/');page.locator('#id_username').fill(account['username']);page.locator('#id_password').fill(account['password'])
  page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/');return c,page
 author,page=login('a')
 if mode in ('retry','broker-retry'):
  name='interruption.json' if mode=='retry' else 'broker-setup-receipt.json'
  receipt=json.loads((OUT/name).read_text());job_id=receipt['job_id'];page.goto(BASE+f'/imports/{job_id}/')
 else:
  src=Path('/run/package.zip').read_bytes();buffer=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(src)) as original,zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as output:
   for info in original.infolist():
    content=original.read(info.filename)
    if mode=='unsupported' and info.filename=='problem.xml':content=content.replace(b'<judging',b'<interactor/><judging')
    if mode=='malformed' and info.filename=='problem.xml':content=b'<problem><judging>broken metadata'
    output.writestr(info,content)
   output.comment=('C07-acceptance-'+mode).encode()
  data=buffer.getvalue()
  page.goto(BASE+'/contest/c1livea/import/')
  page.locator('input[name=package]').set_input_files({'name':'c07-supported.zip','mimeType':'application/zip','buffer':data})
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form[enctype="multipart/form-data"] button[type=submit]').click()
  match=re.fullmatch(r'/imports/(\d+)/',urlsplit(page.url).path);assert match
  job_id=int(match.group(1))
  receipt={'job_id':job_id,'status_url':BASE+f'/imports/{job_id}/'}
  filename='interruption.json' if mode=='queue-only' else mode+'-receipt.json'
  path=OUT/filename;path.write_text(json.dumps(receipt));path.chmod(0o600)
 route=BASE+f'/imports/{job_id}/convert/'
 assert author.request.post(route).status==403
 other,otherpage=login('b')
 assert other.request.get(BASE+f'/imports/{job_id}/').status==404
 token=next((c['value'] for c in other.cookies() if c['name']=='csrftoken'),'')
 assert other.request.post(route,headers={'X-CSRFToken':token}).status==404
 other.close()
 before=int(page.locator('#import-attempt').inner_text())
 # Reproduction refuses to queue a completed job; terminal receipt can be reviewed.
 status=page.locator('#import-status').inner_text().strip()
 if status not in ('succeeded',) and mode!='broker-setup':
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form[action$="/convert/"] button[type=submit]').click()
 if mode=='broker-setup':
  assert status=='uploaded'
  result={'status':'PASS','job_id':job_id,'browser_uploaded_before_broker_failure':True}
 elif mode=='queue-only':
  status=page.locator('#import-status').inner_text().strip();assert status in ('queued','running'),status
  result={'status':'PASS','job_id':job_id,'browser_queue_admitted':True,'observed_state':status}
 else:
  observed=[]
  for _ in range(360):
   status=page.locator('#import-status').inner_text().strip();observed.append(status)
   if status in ('succeeded','failed'):break
   page.wait_for_timeout(500);page.reload(wait_until='domcontentloaded')
  expected='failed' if mode in ('unsupported','malformed') else 'succeeded'
  assert status==expected,(status,observed[-5:])
  attempt=int(page.locator('#import-attempt').inner_text());assert attempt>=1
  for _ in range(2):page.reload();assert page.locator('#import-status').inner_text().strip()==expected;assert int(page.locator('#import-attempt').inner_text())==attempt
  error=page.locator('#import-error').inner_text() if page.locator('#import-error').count() else ''
  assert '/app/' not in error and '/tmp/' not in error
  if expected=='failed':assert 'problem.xml' in error or 'Unsupported' in error
  else:assert 'not been published or judged' in page.locator('#content-body').inner_text()
  result={'status':'PASS','job_id':job_id,'terminal_status':expected,'attempt':attempt,'refresh_preserved_terminal_status':True,'unauthorized_inspection_and_queue_denied':True,'csrf_denied':True,'safe_error':bool(error) if expected=='failed' else None,'observed_states':sorted(set(observed))}
 author.close();browser.close()
(OUT/('browser-'+mode+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print('PASS: C07 browser conversion flow '+mode+'.')
