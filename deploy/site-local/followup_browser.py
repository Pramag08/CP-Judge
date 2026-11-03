"""Focused real-browser checks; isolated temporary identities and private artifacts."""
import json
import os
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000'
OUT=Path('/results')
credentials=json.loads(Path('/run/accounts.json').read_text())
phase=os.environ['B01_FU_PHASE']
result={'phase':phase,'url':BASE,'checks':{},'scope':'native auth/admin/profile and synthetic statement/preview rendering only'}
errors=[];math_assets={};static_errors=[];blocked_hosts=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    result['chromium_version']=browser.version
    context=browser.new_context(viewport={'width':1440,'height':1000})
    def route(request):
        host=urlparse(request.request.url).hostname
        if host=='127.0.0.1':request.continue_()
        else:
            blocked_hosts.append(host)
            request.abort()
    context.route('**/*',route)
    page=context.new_page()
    def page_error(error):
        errors.append(str(error))
        (OUT/'page-errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    page.on('pageerror',page_error)
    def response(resp):
        path=urlparse(resp.url).path
        if '/vendor/mathjax-' in path:math_assets[path]=resp.status
        if path.startswith('/static/') and resp.status>=400:static_errors.append({'path':path,'status':resp.status})
    page.on('response',response)
    def login(role,password=None,valid=True):
        response=page.goto(BASE+'/accounts/login/',wait_until='networkidle')
        assert response.status==200
        page.locator('#id_username').fill(credentials[role]['username'])
        page.locator('#id_password').fill(password or credentials[role]['password'])
        with page.expect_navigation(wait_until='networkidle',timeout=60000):
            page.locator('form.form-area button[type=submit]').click()
        if valid:
            assert page.locator('form[action="/accounts/logout/"]').count()==1
        else:
            assert page.locator('#form-errors').is_visible()
            assert 'Invalid username or password' in page.locator('#form-errors').inner_text()
    def logout():
        page.goto(BASE+'/',wait_until='networkidle')
        page.locator('#user-links > ul > li > a').hover()
        with page.expect_navigation(wait_until='networkidle'):
            page.locator('form[action="/accounts/logout/"] button[type=submit]').click()
        assert page.locator('form[action="/accounts/logout/"]').count()==0
    if phase=='change':
        page.goto(BASE+'/admin/login/',wait_until='networkidle')
        result['checks']['admin_login_without_js_error']='PASS'
        login('participant',password='intentionally-incorrect-followup',valid=False)
        result['checks']['invalid_credentials_rejected']='PASS'
        login('participant')
        page.goto(BASE+'/admin/',wait_until='networkidle')
        assert urlparse(page.url).path.startswith('/admin/login/')
        result['checks']['participant_admin_denied']='PASS'
        logout()
        login('staff')
        page.goto(BASE+'/admin/',wait_until='networkidle')
        assert urlparse(page.url).path=='/admin/'
        assert page.locator('a[href="/admin/auth/user/"]').count()>0
        result['checks']['staff_admin_and_login_logout']='PASS'
        page.goto(BASE+'/admin/auth/user/'+str(credentials['participant']['id'])+'/change/',wait_until='networkidle')
        namespaces=page.evaluate('''() => ({django:typeof django.jQuery==='function',
             global:typeof jQuery==='function',version:django.jQuery.fn.jquery})''')
        assert namespaces['django'] and namespaces['global']
        assert any('/admin/js/jquery.init.js' in (el.get_attribute('src') or '') for el in page.locator('script[src]').all())
        result['checks']['native_django_and_wpadmin_dependency_integration']=namespaces
        page.goto(BASE+'/admin/auth/user/',wait_until='networkidle')
        total=page.locator('tr input.action-select').count()
        assert total>=2
        page.locator('#result_list thead #action-toggle').check()
        assert page.locator('tr input.action-select:checked').count()==total
        page.locator('#result_list thead #action-toggle').uncheck()
        assert page.locator('tr input.action-select:checked').count()==0
        result['checks']['native_bulk_selection']='PASS; real Django Actions API, no backend action submitted'
        page.goto(BASE+'/admin/judge/contest/',wait_until='networkidle')
        link=page.locator('a.action-link').first
        assert link.count()==1
        target=BASE+link.get_attribute('href')
        observed=[]
        def intercept(route):
            req=route.request
            observed.append({'method':req.method,'csrf':bool(parse_qs(req.post_data or '').get('csrfmiddlewaretoken'))})
            route.abort()  # Test transport only: never execute rerating/rejudging.
        page.route(target,intercept)
        with page.expect_request(lambda r:r.url==target):link.click(no_wait_after=True)
        page.wait_for_timeout(200)
        assert observed==[{'method':'POST','csrf':True}],observed
        result['checks']['real_action_link_posts_csrf']='PASS; request intercepted before backend; no contest action executed'
        page.unroute(target,intercept)
        def math(url,label,selector,minimum):
            response=page.goto(url,wait_until='networkidle')
            assert response.status==200
            page.wait_for_function("window.MathJax && typeof MathJax.typesetPromise === 'function'")
            page.evaluate('MathJax.startup.promise')
            page.wait_for_selector('mjx-container')
            page.evaluate('document.fonts.ready')
            assert page.evaluate('MathJax.version')=='3.2.2'
            assert page.locator('mjx-container').count()>=minimum
            assert page.locator(selector).count()>0
            assert page.locator('mjx-merror').count()==0
            assert all(box['width']>0 and box['height']>0 for box in page.locator('mjx-container').evaluate_all('(els)=>els.map(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height}))'))
            page.screenshot(path=str(OUT/(label+'.png')),full_page=True)
            result['checks'][label]={'status':'PASS','rendered_math_nodes':page.locator('mjx-container').count()}
        math(BASE+'/user/'+credentials['participant']['username'],'native_profile_math','mjx-mtable',3)
        math(BASE+'/static/cpjudge-fixtures/b01-followup-statement.html','synthetic_native_statement_math','mjx-msqrt',3)
        math(BASE+'/static/cpjudge-fixtures/b01-followup-preview.html','native_preview_loader_math','mjx-mfrac',3)
        assert any(path.endswith('.woff') for path in math_assets), 'actual math font request not observed'
        assert any('/input/tex/extensions/color.js' in path for path in math_assets), 'local autoload extension not observed'
        logout()
        login('participant')
        page.goto(BASE+'/accounts/password/change/',wait_until='networkidle')
        page.locator('#id_old_password').fill(credentials['participant']['password'])
        page.locator('#id_new_password1').fill(credentials['participant']['changed_password'])
        page.locator('#id_new_password2').fill(credentials['participant']['changed_password'])
        with page.expect_navigation(wait_until='networkidle',timeout=60000):
            page.locator('form').filter(has=page.locator('#id_old_password')).locator('button[type=submit],input[type=submit]').click()
        assert urlparse(page.url).path=='/accounts/password/change/done/',page.url
        result['checks']['native_password_change']='PASS'
        logout()
    else:
        current='changed_password' if phase=='after-verify' else 'password'
        rejected='password' if phase=='after-verify' else 'changed_password'
        login('participant',password=credentials['participant'][rejected],valid=False)
        login('participant',password=credentials['participant'][current])
        result['checks']['password_preserved_after_verify' if phase=='after-verify' else 'explicit_reset_works']='PASS; changed credential accepted, replaced credential rejected'
        logout()
    (OUT/'page-errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    assert not errors, errors
    assert not static_errors,static_errors
    assert set(blocked_hosts)<= {'www.gravatar.com'},blocked_hosts
    assert all(status==200 for status in math_assets.values())
    result.update({'status':'PASS','page_error_count':0,'static_errors':[],
                   'math_assets':math_assets,'external_math_request_attempts':0,
                   'all_external_requests_blocked_before_network':True,
                   'blocked_decoration_hosts':sorted(set(blocked_hosts)),
                   'no_backend_admin_action_executed':True,'actual_import_judging_standings':'NOT TESTED'})
    context.close();browser.close()
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: focused actual Chromium '+phase+' checks; zero page errors; no external math requests.')
