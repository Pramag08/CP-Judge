"""Final focused math regression: no duplicate typesetting, real local fonts/extensions."""
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';OUT=Path('/results')
credentials=json.loads(Path('/run/accounts.json').read_text())
result={'scope':'final native profile and synthetic statement/preview math; no import/judging','checks':{}}
errors=[];assets={};blocked=[];bad=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1440,'height':1000})
    def route(r):
        if urlparse(r.request.url).hostname=='127.0.0.1':r.continue_()
        else:blocked.append(urlparse(r.request.url).hostname);r.abort()
    context.route('**/*',route);page=context.new_page()
    page.on('pageerror',lambda error:errors.append(str(error)))
    def response(r):
        path=urlparse(r.url).path
        if '/vendor/mathjax-' in path:assets[path]=r.status
        if path.startswith('/static/') and r.status>=400:bad.append(path)
    page.on('response',response)
    for label,url in [('profile',BASE+'/user/'+credentials['participant']['username']),
                      ('statement',BASE+'/static/cpjudge-fixtures/b01-followup-statement.html'),
                      ('preview',BASE+'/static/cpjudge-fixtures/b01-followup-preview.html')]:
        response=page.goto(url,wait_until='networkidle');assert response.status==200
        page.wait_for_function("window.MathJax && MathJax.startup && MathJax.startup.promise && typeof MathJax.typesetPromise === 'function'")
        page.evaluate('MathJax.startup.promise');page.wait_for_selector('mjx-container');page.evaluate('document.fonts.ready')
        assert page.locator('mjx-container').count()==3,(label,page.locator('mjx-container').count())
        assert page.locator('mjx-merror').count()==0
        if label!='profile':
            assert page.locator('mjx-container *').evaluate_all("els=>els.some(e=>getComputedStyle(e).color==='rgb(0, 0, 255)')"), 'blue color extension did not render correctly'
        page.screenshot(path=str(OUT/(label+'-final.png')),full_page=True)
        result['checks'][label]={'status':'PASS','equations':3,'duplicate_equations':False,'color_extension_correct':label!='profile'}
    assert all(status==200 for status in assets.values())
    assert any(path.endswith('.woff') for path in assets)
    assert any('/input/tex/extensions/color.js' in path for path in assets)
    assert not errors,errors
    assert not bad,bad
    assert set(blocked)<={'www.gravatar.com'}
    result.update({'status':'PASS','mathjax_version':page.evaluate('MathJax.version'),'page_error_count':0,
                   'local_math_assets':assets,'external_math_requests':0,'blocked_decoration_hosts':sorted(set(blocked)),
                   'actual_import_judging_standings':'NOT TESTED'})
    context.close();browser.close()
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: final profile/statement/preview rendering, 3 equations each, correct color, local fonts/extensions, no JS errors.')
