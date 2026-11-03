"""Actual Chromium scoped author workflow, with existing fixture credentials."""
import json
from pathlib import Path
from datetime import datetime,timedelta,timezone
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path('/results');BASE='http://127.0.0.1:8000';data=json.loads((ROOT/'fixture.json').read_text())
KEY='d01local1';url='/author/contests/'+KEY+'/'
result={'status':'PASS','checks':{},'contest':KEY,'new_judging':False}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 def login(row):
  ctx=b.new_context();ctx.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
  page=ctx.new_page();assert page.goto(BASE+'/accounts/login/').status==200
  page.locator('#id_username').fill(row['email']);page.locator('#id_password').fill(row['password'])
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form.form-area button[type=submit]').click()
  assert '/accounts/login' not in page.url
  return ctx,page
 def post(ctx,path,form={}):
  token=next(c['value'] for c in ctx.cookies() if c['name']=='csrftoken')
  return ctx.request.post(BASE+path,form=dict(form,csrfmiddlewaretoken=token),max_redirects=0)
 contexts={row['role']:login(row) for row in data['accounts']}
 a,page=contexts['author'];participant,pp=contexts['participant'];unrelated,up=contexts['unrelated']
 # Stop on an existing contest; failed attempts resume below without duplicate creation.
 response=a.request.get(BASE+url)
 if response.status==404:
  page.goto(BASE+'/author/contests/create/')
  page.locator('#id_key').fill(KEY);page.locator('#id_name').fill('D01 supervised local contest')
  page.locator('#id_description').fill('Local supervised individual competition.')
  page.locator('#id_display_timezone').fill('Asia/Kolkata')
  day=(datetime.now(timezone.utc)+timedelta(days=2)).strftime('%Y-%m-%d')
  page.locator('#id_start_time').fill(day+' 10:00');page.locator('#id_end_time').fill(day+' 12:00')
  with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Create draft',exact=True).click()
 assert page.goto(BASE+url).status==200
 published='Published — settings locked' in page.content()
 if not published:
  page.locator('#id_name').fill('D01 supervised local contest — edited')
  with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Save draft',exact=True).click()
  assert 'edited' in page.content()
  for ctx in (participant,unrelated):
   assert ctx.request.get(BASE+url).status in (403,404)
   for suffix in ('','publish/','problem/','remove/'):
    assert post(ctx,url+suffix,{'version':data['version'],'label':'A','order':'0'}).status in (403,404)
   assert ctx.request.get(BASE+url+'preview/').status in (403,404)
  result['checks']['participant_unrelated_management_denied']=True
  assert participant.request.get(BASE+'/contest/'+KEY).status==404
  for path in ('/problem/'+data['code'],'/problem/'+data['code']+'/published-assets/statement.css','/api/v2/problem/'+data['code']):
   assert participant.request.get(BASE+path).status in (403,404),path
  result['checks']['draft_direct_problem_api_asset_denied']=True
  assert post(a,url+'publish/').status==409
  result['checks']['missing_problems_block_publish']=True
  assert post(a,url,{'name':'Bad','description':'','display_timezone':'UTC','start_time':'2030-01-01 12:00','end_time':'2030-01-01 11:00'}).status==400
  assert post(a,url,{'format_name':'ioi'}).status==400
  result['checks']['invalid_schedule_crafted_format_denied']=True
  page.goto(BASE+url)
  page.locator('#id_version').select_option(str(data['version']));page.locator('#id_label').fill('Q');page.locator('#id_order').fill('2')
  with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Save problem',exact=True).click()
  page.goto(BASE+url+'preview/')
  text=page.locator('#content-body').inner_text()
  assert 'Asia/Kolkata' in text and 'Q' in text and '20-minute' in text and 'hidden input/output' in text.lower()
  assert str(data['memory_limit']) in text
  page.screenshot(path=ROOT/'preview.png')
  result['checks']['browser_create_edit_select_preview_rules_limits_timezone']=True
  page.goto(BASE+url)
  with page.expect_navigation(wait_until='domcontentloaded'):page.get_by_role('button',name='Publish contest',exact=True).click()
  assert 'Published — settings locked' in page.content(),page.locator('body').inner_text()
  page.screenshot(path=ROOT/'published.png')
  result['checks']['browser_publish_live_readiness_passed']=True
 else:
  raise AssertionError('Existing publication: inspect preserved result rather than claiming a new browser run')
 assert participant.request.get(BASE+'/contest/'+KEY).status==200
 for path in ('/problem/'+data['code'],'/problem/'+data['code']+'/published-assets/statement.css','/api/v2/problem/'+data['code']):
  assert participant.request.get(BASE+path).status in (403,404),path
 assert post(participant,'/contest/'+KEY+'/join').status==403
 assert post(a,url,{'name':'Change published'}).status==403
 result['checks']['scheduled_overview_allowed_problems_denied_no_registration']=True
 assert participant.request.get(BASE+'/problems/').status==404
 for role,(ctx,page) in contexts.items():ctx.close()
 b.close()
(ROOT/'result.json').write_text(json.dumps(result,indent=2));print('PASS: actual scoped author create/edit/select/preview/publish; private future problems and management boundaries.')
