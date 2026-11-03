"""Actual browser admission and native worker results for synthetic sum fixture."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';ROOT=Path('/results')
a=json.loads(Path('/run/accounts.json').read_text())['accounts'];out={'status':'PASS','checks':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 def login(role):
  c=b.new_context();page=c.new_page();page.goto(BASE+'/accounts/login/')
  page.locator('#id_username').fill(a[role]['username']);page.locator('#id_password').fill(a[role]['password'])
  page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/')
  return c,page
 c,page=login('a');url=BASE+'/private-versions/2/probes/';assert page.goto(url).status==200
 for role in ('p','b'):
  if role not in a:continue
  other,op=login(role);assert op.goto(url).status in (403,404);other.close()
 anon=b.new_context();assert anon.request.get(url).status==401;anon.close()
 out['checks']['private_roles_anonymous']=True
 # No CSRF token: browser context request retains login but cannot mutate.
 assert c.request.post(url,data={'name':'denied'}).status==403
 out['checks']['csrf']=True
 runs=[]
 for name,source,verdict in [('accepted-sum','#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b;}', 'AC'),('failing-sum','#include <iostream>\nint main(){std::cout<<0;}', 'WA')]:
  page.goto(url);page.locator('[name=name]').fill(name);page.locator('[name=runtime]').select_option('CPP17');page.locator('[name=source]').fill(source)
  with page.expect_navigation(wait_until='domcontentloaded') as nav:page.get_by_role('button',name='Save private solution').click()
  (ROOT/'last-page.html').write_text(page.content())
  assert nav.value.status==200, ('save status',nav.value.status)
  assert page.locator('.errorlist').count()==0, 'Invalid solution registration form'
  form=page.locator('form').filter(has=page.get_by_role('button',name='Test '+name+' (CPP17)',exact=True)).last
  fields={n:form.locator('[name='+n+']').input_value() for n in ('csrfmiddlewaretoken','digest','solution','solution_digest')}
  stale=dict(fields,digest='0'*64)
  assert c.request.post(url+'run/',form=stale).status==409
  with page.expect_navigation(wait_until='domcontentloaded'):form.get_by_role('button').click()
  seen_pending=False
  for _ in range(120):
   page.reload();row=page.locator('#probes tr').last;status=row.locator('.probe-status').inner_text().strip()
   if status in ('Pending verified worker','Compiling','Grading'):seen_pending=True
   if status==verdict:break
   if 'failed' in status or status in ('IE','CE','AB'):raise AssertionError('Private probe failed; inspect operator logs')
   time.sleep(.5)
  else:raise AssertionError('No genuine verdict before timeout')
  assert row.locator('td').nth(3).inner_text()=='3'
  assert row.locator('td').nth(4).inner_text()==('Yes' if verdict=='AC' else 'No')
  runs.append({'probe_id':int(row.get_attribute('data-probe')),'verdict':verdict,'cases':3,'pending_seen':seen_pending})
 out['checks']['stale_version_rejected']=True;out['runs']=runs
 page.screenshot(path=ROOT/'private-probes.png');b.close()
(ROOT/'result.json').write_text(json.dumps(out,indent=2)+'\n')
print('Browser private probe checks finished.')
