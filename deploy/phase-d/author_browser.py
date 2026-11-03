"""Real Chromium author AC/WA via native version-ready isolated worker."""
import json,time,uuid,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path('/results');BASE='http://127.0.0.1:8000';f=json.loads((ROOT/'fixture.json').read_text())
C='/contest/'+f['contest'];A='/author/contests/'+f['contest'];T=A+'/test/'+f['code']+'/'
result={'status':'RUNNING','contest':f['contest'],'checks':{},'tests':[]}
def save(): (ROOT/'progress.json').write_text(json.dumps(result,indent=2))
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 def login(row):
  ctx=b.new_context();ctx.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
  page=ctx.new_page();page.goto(BASE+'/accounts/login/')
  page.locator('#id_username').fill(row['email']);page.locator('#id_password').fill(row['password'])
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form.form-area button[type=submit]').click()
  assert '/accounts/login' not in page.url,row['role']
  return ctx,page
 def post(ctx,path,form={}):
  token=next(c['value'] for c in ctx.cookies() if c['name']=='csrftoken')
  return ctx.request.post(BASE+path,form=dict(form,csrfmiddlewaretoken=token),max_redirects=0)
 ctxs={row['role']:login(row) for row in f['accounts']};a,ap=ctxs['author'];u,up=ctxs['participant']
 assert ap.goto(BASE+A+'/preview/').status==200
 text=ap.locator('#content-body').inner_text();assert 'Author preview / test mode' in text and 'CPP17' in text and '65536 KiB' in text
 assert ap.get_by_role('link',name='Private author test').count()==1
 assert ap.goto(BASE+'/problem/'+f['code']).status==200
 assert a.request.get(BASE+'/problem/'+f['code']+'/published-assets/statement.css').status==200
 result['checks']['selected_problem_statement_limits_languages_and_private_label']=True;save()
 # Official standings and registration count must remain byte-identical across tests.
 before=u.request.get(BASE+C+'/ranking/');assert before.status==200
 def content(path):
  assert up.goto(BASE+path).status==200
  return up.locator('#content-body').inner_text()
 standing_before=content(C+'/ranking/');overview_before=content(C)
 for expected,field in [('AC','source'),('WA','wrong')]:
  receipt=ROOT/(expected+'-receipt.json')
  if not receipt.exists():
   assert ap.goto(BASE+T).status==200
   ap.locator('textarea[name=source]').fill(f[field])
   key=ap.locator('input[name=request_key]').input_value()
   # Save intent before POST so retries use exactly the same receipt.
   receipt.write_text(json.dumps({'key':key}));receipt.chmod(0o600)
   with ap.expect_navigation(wait_until='domcontentloaded'):ap.get_by_role('button',name='Submit private author test').click()
  else:
   key=json.loads(receipt.read_text())['key']
   assert post(a,T,{'request_key':key,'language':str(f['runtime_id']),'source':f[field]}).status==302
  for _ in range(180):
   ap.goto(BASE+T)
   row=ap.locator('table tr').nth(1);cells=row.locator('td').all_inner_texts()
   if len(cells)>1 and cells[1] in ('AC','WA','CE','IE','RTE','TLE','AB'):break
   time.sleep(.5)
  else:raise AssertionError('No complete private native verdict; preserve receipt.')
  assert cells[1]==expected,cells
  assert int(cells[2])==f['expected_cases'],cells
  result['tests'].append({'test_id':int(cells[0]),'verdict':expected,'cases':int(cells[2])});save()
  assert post(a,T,{'request_key':key,'language':str(f['runtime_id']),'source':f[field]}).status==302
  assert post(a,C+'/problem/'+f['code']+'/submit',{'request_key':str(uuid.uuid4()),'language':str(f['runtime_id']),'source':f[field],'test':'false','virtual':'0'}).status in (403,404)
  assert post(a,'/problem/'+f['code']+'/submit',{'language':str(f['runtime_id']),'source':f[field],'test':'false'}).status==403
 assert content(C+'/ranking/')==standing_before
 assert content(C)==overview_before
 result['checks']['official_standings_registration_count_unchanged']=True
 # Persisted results survive reload and a new authenticated browser session.
 a.close();a,ap=login(next(r for r in f['accounts'] if r['role']=='author'))
 assert ap.goto(BASE+T).status==200
 assert ap.locator('table tr').count()==3
 assert 'AC' in ap.locator('table').inner_text() and 'WA' in ap.locator('table').inner_text()
 ap.screenshot(path=ROOT/'private-author-results.png')
 result['checks']['persisted_private_ac_wa_after_new_login']=True
 for role in ('participant','removed','unrelated'):
  ctx,page=ctxs[role]
  for path in (T,A+'/preview/'):
   assert ctx.request.get(BASE+path).status in (403,404)
   assert post(ctx,path,{'request_key':str(uuid.uuid4()),'language':str(f['runtime_id']),'source':'int main(){}','test':'true','official':'false'}).status in (403,404,405)
  # This existing contest has ended: test flags cannot bypass its deadline or removal.
  assert post(ctx,C+'/problem/'+f['code']+'/submit',{'request_key':str(uuid.uuid4()),'language':str(f['runtime_id']),'source':'int main(){}','test':'true'}).status in (403,404)
  assert post(ctx,'/problem/'+f['code']+'/submit',{'language':str(f['runtime_id']),'source':'int main(){}','test':'true'}).status in (403,404)
 result['checks']['participants_unrelated_author_removed_entry_denied_test_and_deadline_bypass']=True
 result['checks']['author_crafted_official_native_direct_denied']=True
 result['status']='PASS';(ROOT/'result.json').write_text(json.dumps(result,indent=2));b.close()
