"""Real Chromium auth checks; credentials and state only in ignored bind mount."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path('/results')
import sys
recovery=len(sys.argv)>1 and sys.argv[1]=='recovery'
accounts=json.loads((ROOT/('recovery-account.json' if recovery else 'account.json')).read_text())
URL='http://127.0.0.1:8001'
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    def context():
        c=browser.new_context()
        c.route('**/*', lambda route: route.continue_() if route.request.url.startswith(URL+'/') else route.abort())
        return c
    def login(page,password):
        page.goto(URL+'/accounts/login/')
        page.locator('[name=username]').fill(' cpjc1browser ')
        page.locator('[name=password]').fill(password)
        page.locator('button[type=submit]:visible,input[type=submit]:visible').first.click()
        page.wait_for_url('**/accounts/password/change/')
    if recovery:
        old=browser.new_context(storage_state=ROOT/'replacement-session.json')
        assert old.new_page().goto(URL+'/protected/').status==401
        results.append('organizer reset invalidates existing browser session')
    a=context();page=a.new_page()
    login(page,accounts['password'])
    assert page.url.endswith('/accounts/password/change/')
    assert page.goto(URL+'/protected/').url.endswith('/accounts/password/change/')
    results.append('offline local login and forced-change gate')
    changed='Recovery-check-password-3952!' if recovery else 'Browser-check-password-7942!'
    page.locator('[name=old_password]').fill(accounts['password'])
    page.locator('[name=new_password1]').fill(changed)
    page.locator('[name=new_password2]').fill(changed)
    page.locator('button[type=submit]:visible,input[type=submit]:visible').first.click()
    page.wait_for_url('**/accounts/password/change/done/')
    assert page.goto(URL+'/protected/').status==200
    results.append('password change permits authenticated access')
    b=context();other=b.new_page()
    other.goto(URL+'/accounts/login/')
    other.locator('[name=username]').fill('CPJC1BROWSER')
    other.locator('[name=password]').fill(changed)
    other.locator('button[type=submit]:visible,input[type=submit]:visible').first.click()
    other.wait_for_url('**/protected/')
    assert page.goto(URL+'/protected/').status==401
    assert other.goto(URL+'/protected/').status==200
    results.append('replacement browser invalidates prior session')
    # Keep state privately for the recovery phase, never print session cookies.
    b.storage_state(path=ROOT/'replacement-session.json')
    page.screenshot(path=ROOT/'stale-session.png')
    browser.close()
(ROOT/('recovery-browser.json' if recovery else 'browser.json')).write_text(json.dumps({'status':'PASS','checks':results,'isolated_port':8001},indent=2)+'\n')
print('Chromium identity checks passed against isolated test database.')
