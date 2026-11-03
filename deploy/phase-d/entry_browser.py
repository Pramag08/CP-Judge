"""Real Chromium entry/withdrawal/late-entry/removal/DQ and one official AC."""
import json,time,uuid,re
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path('/results');BASE='http://127.0.0.1:8000';f=json.loads((ROOT/'fixture.json').read_text());f['source']=f['source'].replace('\r\n','\n').replace('\r','\n');C='/contest/'+f['contest']
result=json.loads((ROOT/'progress.json').read_text()) if (ROOT/'progress.json').exists() else {'contest':f['contest'],'checks':{}}
result['status']='RUNNING'
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
 ctxs={row['role']:login(row) for row in f['accounts']};a,ap=ctxs['author'];u,up=ctxs['participant'];late,lp=ctxs['late'];other,op=ctxs['unrelated']
 participant=next(row for row in f['accounts'] if row['role']=='participant')
 if not result['checks'].get('browser_prestart_register_withdraw_reregister_idempotent_native_leave_csrf_author_conflict'):
  assert datetime.now(timezone.utc)<datetime.fromisoformat(f['start']),'Pre-start fixture expired; do not rewrite its schedule.'
  assert up.goto(BASE+C).status==200
  assert u.request.post(BASE+C+'/register',form={}).status==403
  with up.expect_navigation(wait_until='domcontentloaded'):up.get_by_role('button',name='Register',exact=True).click()
  assert 'Your status: active' in up.locator('body').inner_text()
  assert post(u,C+'/register').status==302
  with up.expect_navigation(wait_until='domcontentloaded'):up.get_by_role('button',name='Deregister',exact=True).click()
  assert 'Your status: withdrawn' in up.locator('body').inner_text()
  with up.expect_navigation(wait_until='domcontentloaded'):up.get_by_role('button',name='Register',exact=True).click()
  assert post(a,C+'/join',{'virtual':'0'}).status==403
  assert post(u,C+'/leave').status==302
  assert 'Your status: active' in u.request.get(BASE+C).text()
  assert u.request.get(BASE+'/problem/'+f['code']).status==404
  result['checks']['browser_prestart_register_withdraw_reregister_idempotent_native_leave_csrf_author_conflict']=True;save()
 assert ap.goto(BASE+C+'/roster').status==200
 assert participant['email'] in ap.locator('#content-body').inner_text()
 entryrow=ap.locator('tr[data-entry]').filter(has_text=participant['username']);entry_id=entryrow.get_attribute('data-entry');result['entry_id']=int(entry_id)
 for ctx in (u,other):
  assert ctx.request.get(BASE+C+'/roster').status in (403,404)
  assert post(ctx,C+'/entries/'+entry_id+'/sanction',{'action':'remove','reason':'unauthorized'}).status in (403,404)
 assert all(row['email'] not in u.request.get(BASE+C).text() for row in f['accounts'] if row['role']!='participant')
 result['checks']['roster_private_scoped_management']=True;save()
 if not result['checks'].get('actual_clock_late_registration_and_no_post_start_withdrawal'):
  # Wait on the actual stored UTC start; no live clock or schedule mutation.
  while datetime.now(timezone.utc)<datetime.fromisoformat(f['start']):time.sleep(.4)
  assert lp.goto(BASE+C).status==200
  with lp.expect_navigation(wait_until='domcontentloaded'):lp.get_by_role('button',name='Register',exact=True).click()
  assert 'Your status: active' in lp.locator('body').inner_text()
  assert post(u,C+'/deregister').status==403 and post(late,C+'/deregister').status==403
  assert post(u,C+'/join').status==302
  assert u.request.get(BASE+'/problem/'+f['code']).status==200
  result['checks']['actual_clock_late_registration_and_no_post_start_withdrawal']=True;save()
 assert post(u,C+'/join').status==302
 # A single genuine native form POST, tracked before waiting for its verdict.
 receipt=ROOT/'submission.json'
 if not receipt.exists():
  assert up.goto(BASE+C+'/problem/'+f['code']+'/submit',wait_until='networkidle').status==200
  up.wait_for_function("Boolean(window.ace_source && typeof window.ace_source.getSession === 'function')")
  up.locator('#id_language').select_option(str(f['runtime_id']),force=True)
  up.wait_for_function('window.jQuery.active===0')
  up.evaluate('(source)=>{window.ace_source.getSession().setValue(source);document.getElementById("id_source").value=source;}',f['source'])
  observed=up.locator('#id_source').input_value()
  (ROOT/'source-observed.txt').write_text(observed)
  assert observed==f['source'], {'expected_length':len(f['source']),'actual_length':len(observed)}
  assert up.evaluate("document.getElementById('problem_submit').checkValidity()")
  key=up.locator('input[name=request_key]').input_value()
  (ROOT/'intent.json').write_text(json.dumps({'key':key}));(ROOT/'intent.json').chmod(0o600)
  with up.expect_navigation(wait_until='domcontentloaded'):up.locator('#problem_submit input[type=submit]').click()
  match=re.search(r'/submission/(\d+)',up.url);assert match,up.locator('body').inner_text()
  sid=int(match[1]);receipt.write_text(json.dumps({'id':sid,'key':key}));receipt.chmod(0o600);result['submission_id']=sid;save()
 else:
  saved=json.loads(receipt.read_text());sid=saved['id'];key=saved['key'];result['submission_id']=sid
  up.goto(BASE+'/submission/'+str(sid))
 # Native authenticated polling only; actual result is independently checked in SQL.
 for _ in range(180):
  up.reload(wait_until='domcontentloaded')
  text=up.locator('body').inner_text()
  if re.search(r'\bAC\b|Accepted',text):break
  time.sleep(.5)
 else:raise AssertionError('Native AC not observed; retain admitted receipt for diagnosis.')
 assert post(u,C+'/problem/'+f['code']+'/submit',{'request_key':key,'language':str(f['runtime_id']),'source':f['source'].replace('\n','\r\n')}).status==302
 result['checks']['one_actual_official_browser_ac_and_idempotent_retry']=True;save()
 assert ap.goto(BASE+C+'/roster').status==200
 row=ap.locator('tr[data-entry="'+entry_id+'"]');row.locator('input[name=reason]').fill('D11 browser removal acceptance')
 with ap.expect_navigation(wait_until='domcontentloaded'):row.get_by_role('button',name='Remove',exact=True).click()
 assert ap.goto(BASE+C+'/ranking/').status==200
 assert 'Removed' in ap.locator('#content-body').inner_text()
 assert participant['email'] not in ap.locator('#content-body').inner_text()
 ap.screenshot(path=ROOT/'removed-standings.png')
 for path in (C,C+'/register',C+'/join',C+'/ranking/',C+'/roster','/problem/'+f['code'],'/problem/'+f['code']+'/submit',C+'/problem/'+f['code']+'/submit','/problem/'+f['code']+'/published-assets/statement.css','/submission/'+str(sid),'/src/'+str(sid)+'/raw','/widgets/submission_testcases?id='+str(sid),'/cpjudge/events/contest_'+str(f['contest_id'])):
  assert u.request.get(BASE+path).status in (403,404,405),path
 assert post(u,C+'/join').status in (403,404)
 assert post(u,C+'/problem/'+f['code']+'/submit',{'request_key':str(uuid.uuid4()),'language':str(f['runtime_id']),'source':f['source']}).status in (403,404)
 assert sid not in [r.get('id') for r in u.request.get(BASE+'/cpjudge/events/submissions').json()['messages']]
 # An existing unrelated contest/problem remains available to this same account.
 assert u.request.get(BASE+'/problem/pv000000000000000001').status==200
 assert late.request.get(BASE+C).status==200 and late.request.get(BASE+'/problem/'+f['code']).status==200
 result['checks']['removal_native_direct_assets_submit_poll_denied_other_contest_unaffected']=True;save()
 ap.goto(BASE+C+'/roster');row=ap.locator('tr[data-entry="'+entry_id+'"]');row.locator('input[name=reason]').fill('D11 browser disqualification acceptance')
 with ap.expect_navigation(wait_until='domcontentloaded'):row.get_by_role('button',name='Disqualify',exact=True).click()
 assert ap.goto(BASE+C+'/ranking/').status==200
 assert 'DQ' in ap.locator('#content-body').inner_text()
 ap.screenshot(path=ROOT/'dq-standings.png')
 result['checks']['browser_reasoned_removal_then_dq_standings']=True;save()
 for ctx,page in ctxs.values():ctx.close()
 b.close()
result['status']='PASS'
(ROOT/'result.json').write_text(json.dumps(result,indent=2));print('PASS: actual registration/withdrawal/late entry, one official AC, scoped removal/DQ, privacy and bypass checks.')
