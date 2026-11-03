"""B10/B11 native Chromium journeys; raw DOM/source/cookies stay under build/."""
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, urlparse
from playwright.sync_api import sync_playwright

OUT=Path('/results'); CONFIG=json.loads(Path('/run/probes/config.json').read_text())
ACCOUNTS=json.loads(Path('/run/accounts.json').read_text())
BASE='http://127.0.0.1:8000'; CODE='pv000000000000000001'; KEY='b10b11local1'
posts=[]; sessions=[]; contexts=[]; errors=[]

def login(browser, account):
    ctx=browser.new_context(viewport={'width':1440,'height':1000});contexts.append(ctx)
    ctx.route('**/*',lambda r:r.continue_() if urlparse(r.request.url).hostname=='127.0.0.1' else r.abort())
    page=ctx.new_page(); page.on('dialog',lambda dialog:dialog.accept()); page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/accounts/login/',wait_until='networkidle')
    page.locator('#id_username').fill(account['username']);page.locator('#id_password').fill(account['password'])
    with page.expect_navigation(wait_until='networkidle'):
        page.locator('form.form-area button[type=submit]').click()
    assert page.locator('form[action="/accounts/logout/"]').count()==1
    def request(r):
        if r.method=='POST' and urlparse(r.url).path=='/problem/'+CODE+'/submit':
            data=parse_qs(r.post_data or '',keep_blank_values=True)
            posts.append({'username':account['username'],'language':data['language'][0],
                'source_sha256':hashlib.sha256(data['source'][0].encode()).hexdigest(),
                'canonical_sha256':hashlib.sha256(data['source'][0].replace('\r\n','\n').strip().encode()).hexdigest(),
                'csrf':bool(data.get('csrfmiddlewaretoken'))})
    page.on('request',request)
    return page

def prepare(page,label):
    response=page.goto(BASE+'/problem/'+CODE+'/submit',wait_until='networkidle'); assert response.status==200
    page.wait_for_function("Boolean(window.ace_source && typeof window.ace_source.getSession === 'function')")
    with page.expect_response(lambda r:urlparse(r.url).path=='/widgets/template' and r.status==200) as response:
        page.locator('#id_language').select_option(label='GNU C++23',force=True)
    response.value.finished();page.wait_for_function('window.jQuery.active===0')
    source=Path('/run/probes/'+label+'.cpp').read_text()
    page.evaluate('s=>window.ace_source.getSession().setValue(s)',source)
    assert page.locator('#id_source').input_value()==source

receipts=json.loads((OUT/'receipts.json').read_text()) if (OUT/'receipts.json').exists() else []
def receipt(page, label, name):
    page.wait_for_url(re.compile(BASE+r'/submission/\d+/?$'),timeout=60000)
    sid=int(re.search(r'/submission/(\d+)',page.url).group(1))
    row={'id':sid,'label':label,'username':ACCOUNTS[name]['username']}
    receipts.append(row);(OUT/'receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    return sid

def done(page,label):
    if label=='ce':
        page.wait_for_function("document.querySelector('#test-cases').textContent.includes('Compilation Error')",timeout=120000)
        assert page.locator('#test-cases .case-row').count()==0
    else:
        page.wait_for_function("document.querySelectorAll('#test-cases .case-row').length===103 && document.querySelector('#test-cases').textContent.includes('Final score:')",timeout=120000)
        statuses=[s.strip() for s in page.locator('#test-cases .case-row td:nth-child(2) span').all_text_contents()]
        expected=CONFIG['wrong_cases'] if label=='wrong' else ['AC']*103
        assert statuses==expected
    (OUT/('submission-'+str(receipts[-1]['id'])+'.html')).write_text(page.content())


def standings(page, tag):
    response=page.goto(BASE+'/contest/'+KEY+'/ranking/',wait_until='networkidle');assert response.status==200
    rows=[]
    for row in page.locator('tr[id^="user-b10tmp"]').all():
        rows.append({'username':row.get_attribute('id')[5:],'rank':int(row.locator('td').first.inner_text()),
                     'solved':int(row.locator('td.user-points > a').inner_text().splitlines()[0]),
                     'penalty_display':row.locator('td.user-points .solving-time').inner_text(),
                     'problem_cell':row.locator('td').nth(3).inner_text()})
    page.screenshot(path=str(OUT/(tag+'.png')),full_page=True)
    (OUT/(tag+'.html')).write_text(page.content())
    return rows

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    result={}
    try:
        action=CONFIG['action']
        if action=='b10':
            anonymous=browser.new_context();contexts.append(anonymous);page=anonymous.new_page()
            assert page.goto(BASE+'/contest/'+KEY,wait_until='networkidle').status==403
            assert page.goto(BASE+'/problem/'+CODE,wait_until='networkidle').status in (403,404)
            outsider=login(browser,ACCOUNTS['outsider'])
            assert outsider.goto(BASE+'/contest/'+KEY,wait_until='networkidle').status==403
            pages={}
            # Reverse account creation order deliberately: stable tie rows follow entry ID.
            for name in ('b','a'):
                page=login(browser,ACCOUNTS[name]);pages[name]=page
                assert page.goto(BASE+'/problem/'+CODE,wait_until='networkidle').status in (403,404)
                assert page.goto(BASE+'/contest/'+KEY,wait_until='networkidle').status==200
                with page.expect_navigation(wait_until='networkidle'):
                    page.locator('form[action="/contest/'+KEY+'/join"] input[type=submit]').click()
                assert page.goto(BASE+'/problem/'+CODE,wait_until='networkidle').status==200
                assert page.locator('.imported-statement').count() or page.locator('.problem-statement').count()
                prepare(page,'wrong')
                with page.expect_navigation(wait_until='domcontentloaded'):
                    page.locator('#problem_submit input[type=submit]').click()
                receipt(page,'wrong',name);done(page,'wrong')
            result={'status':'PASS','denied_anonymous_and_nonallowlisted':True,'denied_problem_before_join':True,
                    'two_native_joins':True,'two_separate_form_submissions':True,
                    'standings':standings(pages['a'],'b10-standings')}
        elif action in ('ce','after'):
            label='ce' if action=='ce' else 'wrong'
            page=login(browser,ACCOUNTS['a']);prepare(page,label)
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator('#problem_submit input[type=submit]').click()
            receipt(page,label,'a');done(page,label)
            result={'standings':standings(page,'ce-standings')}
        elif action=='pair':
            pages={name:login(browser,ACCOUNTS[name]) for name in ('a','b')}
            for page in pages.values():prepare(page,'accepted')
            # Schedule genuine native clicks together; ranking still uses stored server receipts.
            from datetime import datetime
            target=time.time()+1+(datetime.fromisoformat(CONFIG['start']).timestamp()+0.15-time.time())%1
            for page in pages.values():page.evaluate("target=>setTimeout(()=>document.querySelector('#problem_submit input[type=submit]').click(),Math.max(0,target-Date.now()))",target*1000)
            for name,page in pages.items():receipt(page,'accepted',name)
            for page in pages.values():done(page,'accepted')
            result={'standings':standings(pages['a'],'pair-standings')}
        elif action=='persistence':
            pages={name:login(browser,account) for name,account in ACCOUNTS.items()}
            result={'authenticated_account_roles':list(pages), 'standings':standings(pages['a'],'persistent-standings')}
        elif action=='restart-submit':
            page=login(browser,ACCOUNTS['b']);prepare(page,'accepted')
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator('#problem_submit input[type=submit]').click()
            sid=receipt(page,'accepted','b');done(page,'accepted')
            page.goto(BASE+'/submissions/user/'+ACCOUNTS['b']['username']+'/',wait_until='networkidle')
            row=page.locator('[id="'+str(sid)+'"].submission-row')
            assert row.locator('.status').inner_text().strip()=='AC'
            result={'displayed_verdict':'AC','completed_case_count':103,'standings':standings(page,'post-restart-standings')}
        elif action=='standings':
            page=login(browser,ACCOUNTS['a'])
            result={'standings':standings(page,'standings')}
        else:raise AssertionError(action)
        assert not errors,errors
        result.update({'posts':posts,'receipts':receipts,'page_errors':errors})
        (OUT/'browser.json').write_text(json.dumps(result,indent=2)+'\n')
    finally:
        for i,ctx in enumerate(contexts):
            if not (OUT/'browser.json').exists() and ctx.pages:
                (OUT/('diagnostic-'+str(i)+'.html')).write_text(ctx.pages[-1].content())
            sessions.extend(c['value'] for c in ctx.cookies() if c['name']=='sessionid')
        (OUT/'sessions.json').write_text(json.dumps(sessions))
        browser.close()
print('PASS: native contest browser action '+CONFIG['action'])
