"""Actual Chromium navigation and forms. Credentials/artifacts stay private."""
import json
import os
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

BASE = os.environ.get('B01_URL', 'http://site:8000')
OUT = Path('/results')
credentials = json.loads(Path('/run/accounts.json').read_text())
result = {'url': BASE, 'scope': 'real headless Chromium browser; standard native pages', 'checks': {}}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    result['chromium_version'] = browser.version
    result['playwright_version'] = version('playwright')
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    # Only this disposable website is visited; remote decoration is not a baseline dependency.
    context.route('**/*', lambda route: route.continue_() if urlparse(route.request.url).hostname == urlparse(BASE).hostname else route.abort())
    page = context.new_page()
    assets = []
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('response', lambda response: assets.append({'path':urlparse(response.url).path,'status':response.status})
            if '/static/' in response.url else None)
    response = page.goto(BASE + '/accounts/login/', wait_until='networkidle')
    assert response.status == 200
    page.wait_for_selector('input#id_username')
    page.screenshot(path=str(OUT/'login-styled.png'), full_page=True)
    visual = page.evaluate('''() => ({
        loadedStyles: [...document.styleSheets].filter(s => s.href && s.href.includes('/static/')).length,
        bodyFont: getComputedStyle(document.body).fontFamily,
        navPosition: getComputedStyle(document.querySelector('nav')).position,
        formWidth: document.querySelector('.auth-flow-form').getBoundingClientRect().width,
        inputVisible: document.querySelector('#id_username').getBoundingClientRect().width > 100,
        jqueryLoaded: typeof window.jQuery === 'function'
    })''')
    assert visual['loadedStyles'] >= 3 and visual['navPosition'] == 'fixed', visual
    assert visual['inputVisible'] and visual['jqueryLoaded'], visual
    assert assets and all(item['status']==200 for item in assets), assets
    result['checks']['styled_login'] = {'status':'PASS', 'computed':visual}
    home_response=page.goto(BASE+'/', wait_until='networkidle')
    assert home_response.status == 200
    assert page.locator('nav').is_visible() and page.locator('#content').count() > 0
    page.screenshot(path=str(OUT/'home-styled.png'),full_page=True)
    result['checks']['home_loads'] = 'PASS'

    def login(role, valid=True):
        page.goto(BASE+'/accounts/login/',wait_until='domcontentloaded')
        page.locator('#id_username').fill(credentials[role]['username'])
        page.locator('#id_password').fill(credentials[role]['password'] if valid else 'deliberately-invalid-b01-password')
        with page.expect_navigation(wait_until='domcontentloaded', timeout=60000):
            page.locator('form.form-area button[type=submit]').click()
        if valid:
            page.wait_for_selector('form[action="/accounts/logout/"]', state='attached')
            assert '/accounts/login/' not in page.url
        else:
            assert page.locator('#form-errors').is_visible()
            assert 'Invalid username or password' in page.locator('#form-errors').inner_text()
            assert page.locator('form[action="/accounts/logout/"]').count()==0

    def logout():
        page.goto(BASE+'/',wait_until='domcontentloaded')
        page.locator('#user-links > ul > li > a').hover()
        with page.expect_navigation(wait_until='domcontentloaded'):
            page.locator('form[action="/accounts/logout/"] button[type=submit]').click()
        assert page.locator('form[action="/accounts/logout/"]').count()==0
        response=page.goto(BASE+'/user',wait_until='domcontentloaded')
        assert urlparse(page.url).path.startswith('/accounts/login'), page.url

    login('participant', valid=False)
    result['checks']['incorrect_credentials_rejected']='PASS'
    login('participant')
    result['checks']['participant_login']='PASS'
    assert page.locator('#user-links a[href="/admin/"]').count()==0
    response=page.goto(BASE+'/admin/',wait_until='domcontentloaded')
    assert urlparse(page.url).path.startswith('/admin/login/'), page.url
    assert page.locator('#content-main .app-auth').count()==0
    result['checks']['participant_admin_denied']='PASS (redirect to admin authentication; no admin index)'
    logout()
    result['checks']['participant_logout_and_protected_redirect']='PASS'
    login('staff')
    result['checks']['staff_login']='PASS'
    response=page.goto(BASE+'/admin/',wait_until='domcontentloaded')
    assert response.status==200 and urlparse(page.url).path=='/admin/'
    assert page.locator('a[href="/admin/auth/user/"]').count() > 0
    result['checks']['staff_admin_access']='PASS'
    logout()
    result['checks']['staff_logout_and_protected_redirect']='PASS'
    result['static_responses']=sorted({(a['path'],a['status']) for a in assets})
    result['page_error_count']=len(errors)
    # Detailed browser error strings can contain user identifiers: keep private.
    (OUT/'page-errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    result['website_to_judge']='NOT TESTED'
    result['status']='PASS'
    context.close()
    browser.close()
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: styled browser pages; invalid login, staff/participant login/logout and participant admin denial.')
