"""Actual private native problem page, compared with package HTML in Chromium."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse
import zipfile
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8000'
CODE = 'pv000000000000000001'
OUT = Path('/results')
credentials = json.loads(Path('/run/accounts.json').read_text())['participant']
with zipfile.ZipFile('/run/package.zip') as archive:
    names = [n for n in archive.namelist() if n.startswith('statements/') and n.endswith('.html')]
    assert len(names) == 1
    original = archive.read(names[0]).decode()
body = re.split(r'<body[^>]*>', original, flags=re.I)[1].split('</BODY>')[0]
expected_math = re.findall(r'\$\$\$(.*?)\$\$\$', body, flags=re.S)
assert len(expected_math) == 30
errors, blocked, assets, blocked_details = [], [], {}, []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    def route(r):
        if urlparse(r.request.url).hostname == '127.0.0.1':
            r.continue_()
        else:
            blocked.append(urlparse(r.request.url).hostname); blocked_details.append({'url':r.request.url,'type':r.request.resource_type}); r.abort()
    context.route('**/*', route)
    page = context.new_page()
    cdp = context.new_cdp_session(page); cdp.send('Network.enable')
    def network(event):
        if 'fonts.googleapis.com' in event.get('request', {}).get('url', ''):
            (OUT / 'font-initiator.json').write_text(json.dumps(event.get('initiator', {})))
    cdp.on('Network.requestWillBeSent', network)
    page.on('pageerror', lambda error: errors.append(str(error)))
    def response(r):
        path = urlparse(r.url).path
        if '/vendor/mathjax-' in path or '/statement-assets/' in path:
            assets[path] = r.status
    page.on('response', response)
    try:
        assert page.goto(BASE + '/problem/' + CODE).status == 404
        assert context.request.get(BASE + '/problem/' + CODE + '/statement-assets/statement.css').status == 404
        page.goto(BASE + '/accounts/login/', wait_until='networkidle')
        page.locator('#id_username').fill(credentials['username'])
        page.locator('#id_password').fill(credentials['password'])
        with page.expect_navigation(wait_until='networkidle'):
            page.locator('form.form-area button[type=submit]').click()
        assert page.locator('form[action="/accounts/logout/"]').count() == 1
        result = page.goto(BASE + '/problem/' + CODE, wait_until='networkidle'); assert result.status == 200
        page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise')
        page.evaluate('MathJax.startup.promise')
        (OUT / 'initial-render.html').write_text(page.content())
        (OUT / 'math-diagnostic.json').write_text(json.dumps(page.evaluate("({all:document.querySelectorAll('mjx-container').length, imported:document.querySelectorAll('.b06-imported mjx-container').length, wrappers:document.querySelectorAll('.b06-imported').length, text:document.querySelector('.b06-imported')?.textContent, errors:document.querySelectorAll('mjx-merror').length})")))
        page.screenshot(path=str(OUT / 'initial-render.png'), full_page=True)
        page.wait_for_function("document.querySelectorAll('.b06-imported mjx-container').length === 30")
        page.evaluate('document.fonts.ready')
        assert page.locator('.b06-imported mjx-merror').count() == 0
        observed = page.evaluate('Array.from(MathJax.startup.document.math).map(item => item.math)')
        assert observed == expected_math, ('math differs', len(observed), len(expected_math))
        comparison = page.evaluate(r'''source => {
          const doc = new DOMParser().parseFromString(source, 'text/html');
          const normalized = s => s.replace(/\s+/g,' ').replace(/\s*([(),.;:])\s*/g,'$1').trim();
          const out = {};
          for (const section of ['legend','input-specification','output-specification','note']) {
            const expected=doc.querySelector('.'+section).textContent.replace(/\$\$\$(.*?)\$\$\$/gs,' MATH ');
            const clone=document.querySelector('.b06-imported .'+section).cloneNode(true);
            clone.querySelectorAll('mjx-container').forEach(e=>e.replaceWith(' MATH '));
            out[section] = normalized(expected) === normalized(clone.textContent);
          }
          const srcInput=doc.querySelector('.sample-test .input pre');
          const sourceInput=srcInput.dataset.content || [...srcInput.querySelectorAll('div')].map(e=>e.textContent).join('\n');
          const sourceOutput=doc.querySelector('.sample-test .output pre').textContent;
          out.sample_input = normalized(sourceInput)===normalized(document.querySelector('.b06-imported .input pre').textContent);
          out.sample_output = normalized(sourceOutput)===normalized(document.querySelector('.b06-imported .output pre').textContent);
          out.no_executable_import = ![...document.querySelectorAll('.b06-imported script,.b06-imported iframe,.b06-imported [style],.b06-imported [src],.b06-imported [href],.b06-imported [onclick]')].some(e=>!e.closest('mjx-container'));
          out.native_layout = !!document.querySelector('nav') && getComputedStyle(document.querySelector('nav')).position==='fixed';
          return out;
        }''', body)
        assert all(comparison.values()), comparison
        css = context.request.get(BASE + '/problem/' + CODE + '/statement-assets/statement.css')
        assert css.status == 200 and css.headers['cache-control'] == 'private, no-store'
        assert css.headers['x-content-type-options'] == 'nosniff'
        assert css.body().startswith(b'.b06-imported')
        assert all(status == 200 for status in assets.values()), assets
        assert any(path.endswith('.woff') for path in assets)
        assert not errors, errors
        (OUT / 'blocked-details.json').write_text(json.dumps(blocked_details))
        assert set(blocked) <= {'www.gravatar.com'}, blocked
        denies = 0
        for i in range(1, 104):
            for suffix in ('in', 'out'):
                assert context.request.get(BASE + '/problem/' + CODE + '/data/' + str(i) + '.' + suffix).status == 404
                denies += 1
        for path in ('data.zip','init.yml','checker.cpp','testlib.h','solutions/reference.cpp'):
            assert context.request.get(BASE + '/problem/' + CODE + '/data/' + path).status == 404
            assert context.request.get(BASE + '/static/problems/' + CODE + '/' + path).status == 404
            denies += 2
        for asset in ('../data.zip','data.zip','%2e%2e%2fdata.zip'):
            assert context.request.get(BASE + '/problem/' + CODE + '/statement-assets/' + asset).status == 404
            denies += 1
        page.screenshot(path=str(OUT / 'real-problem.png'), full_page=True)
        (OUT / 'rendered.html').write_text(page.content())
        result = {'status': 'PASS', 'problem_url': BASE + '/problem/' + CODE,
                  'scope': 'real Chromium native private problem page and native ordinary login',
                  'source_sections_and_samples_match': comparison, 'math_expressions': 30,
                  'math_source_exact_order_match': True, 'mathjax_version': page.evaluate('MathJax.version'),
                  'page_error_count': 0, 'private_data_route_denials': denies,
                  'anonymous_problem_css_denied': True, 'scoped_css_authenticated': True,
                  'local_assets': assets, 'blocked_decoration_hosts': sorted(set(blocked)),
                  'external_imported_requests': 0, 'judging': 'NOT TESTED'}
        (OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        page.goto(BASE + '/', wait_until='domcontentloaded')
        page.locator('#user-links > ul > li > a').hover()
        with page.expect_navigation(wait_until='domcontentloaded'):
            page.locator('form[action="/accounts/logout/"] button[type=submit]').click()
    finally:
        (OUT / 'sessions.json').write_text(json.dumps([c['value'] for c in context.cookies() if c['name'] == 'sessionid']))
        context.close(); browser.close()
print('PASS: real statement/source/math/sample comparison, restricted assets and data-route denials.')
