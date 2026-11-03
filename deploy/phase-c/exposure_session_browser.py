"""Private browser check for server-side session revocation and unchanged login."""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000'
OUT=Path('/results')
account=json.loads(Path('/run/legacy.json').read_text())['participant']
mode=os.environ.get('MODE')

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context()
    context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(BASE+'/') else r.abort())
    page=context.new_page()
    if mode=='capture':
        page.goto(BASE+'/accounts/login/')
        page.locator('#id_username').fill(account['username'])
        page.locator('#id_password').fill(account['password'])
        page.locator('form.form-area button[type=submit]').click()
        page.wait_for_url('**/contests/')
        assert page.request.get(BASE+'/edit/profile/').status==200
        cookies=[c for c in context.cookies() if c['name']=='sessionid']
        assert len(cookies)==1
        target=OUT/'pre-revocation-cookie.json'
        target.write_text(json.dumps(cookies))
        target.chmod(0o600)
        result={'status':'PASS','authenticated_cookie_captured':True}
    elif mode=='verify':
        cookies=json.loads((OUT/'pre-revocation-cookie.json').read_text())
        context.add_cookies(cookies)
        stale=page.request.get(BASE+'/edit/profile/').status
        assert stale in (401,403),f'Old server-side session unexpectedly valid: {stale}'
        page.goto(BASE+'/accounts/login/')
        page.locator('#id_username').fill(account['username'])
        page.locator('#id_password').fill(account['password'])
        page.locator('form.form-area button[type=submit]').click()
        page.wait_for_url('**/contests/')
        assert page.request.get(BASE+'/edit/profile/').status==200
        result={'status':'PASS','previous_browser_session_requires_login':True,'existing_password_still_works':True}
    else:
        raise ValueError('Expected capture or verify mode')
    browser.close()

(OUT/('exposure-session-'+mode+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print('PASS: exposure remediation browser session check.')
