"""One genuine native participant form POST, then native displayed case/verdict checks."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET
import zipfile
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8000'
CODE = 'pv000000000000000001'
OUT = Path('/results')
credentials = json.loads(Path('/results/accounts.json').read_text())['accounts']['p']
probe = None
reference = Path('/run/reference.cpp').read_text()
resume = json.loads(Path('/run/receipt.json').read_text()) if Path('/run/receipt.json').exists() else None
expected_sha = hashlib.sha256(reference.strip().encode()).hexdigest()
posts, errors, blocked = [], [], []
polls=[]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    def route(r):
        if urlparse(r.request.url).hostname == '127.0.0.1':
            r.continue_()
        else:
            blocked.append(urlparse(r.request.url).hostname); r.abort()
    context.route('**/*', route)
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    def request(r):
        if r.method == 'POST' and urlparse(r.url).path == '/problem/' + CODE + '/submit':
            body = parse_qs(r.post_data or '', keep_blank_values=True)
            assert 'source' in body and 'language' in body
            posts.append({'method': 'POST', 'path': urlparse(r.url).path,
                          'language_id': body['language'][0], 'source_sha256': hashlib.sha256(body['source'][0].encode()).hexdigest(),
                          'source_canonical_sha256': hashlib.sha256(body['source'][0].replace('\r\n', '\n').strip().encode()).hexdigest(),
                          'source_bytes': len(body['source'][0].encode()), 'csrf_field_present': bool(body.get('csrfmiddlewaretoken'))})
            (OUT / 'browser-post.json').write_text(json.dumps(posts[-1], indent=2) + '\n')
    page.on('request', request)
    page.on('response', lambda r: polls.append(r.status) if '/cpjudge/events/sub_' in r.url else None)
    try:
        page.goto(BASE + '/accounts/login/', wait_until='networkidle')
        page.locator('#id_username').fill(credentials['username'])
        page.locator('#id_password').fill(credentials['password'])
        with page.expect_navigation(wait_until='networkidle'):
            page.locator('form.form-area button[type=submit]').click()
        assert page.locator('form[action="/accounts/logout/"]').count() == 1
        # Native join retains an individual official entry and the existing contest clock.
        page.goto(BASE+'/contest/c1livea', wait_until='domcontentloaded')
        join=page.locator('form[action="/contest/c1livea/join"] input[type=submit]')
        if join.count():
            with page.expect_navigation(wait_until='domcontentloaded'):join.click()
        else:
            assert page.locator('form[action="/contest/c1livea/leave"]').count()==1
        if resume is None:
            response = page.goto(BASE + '/problem/' + CODE + '/submit', wait_until='networkidle')
            assert response.status == 200 and page.locator('#problem_submit').count() == 1
            page.wait_for_function("Boolean(window.ace_source && typeof window.ace_source.getSession === 'function')")
            with page.expect_response(lambda r: urlparse(r.url).path == '/widgets/template' and r.status == 200) as template:
                page.locator('#id_language').select_option(label='GNU C++23', force=True)
            template.value.finished()
            page.wait_for_function('window.jQuery.active === 0')
            label = page.locator('#id_language option:checked').inner_text()
            language_id = page.locator('#id_language').input_value()
            assert label == 'GNU C++23'
            page.evaluate('source => window.ace_source.getSession().setValue(source)', reference)
            assert page.evaluate('window.ace_source.getSession().getValue()') == reference
            assert page.locator('#id_source').input_value() == reference
            page.screenshot(path=str(OUT / 'native-submit-form.png'), full_page=True)
            with page.expect_navigation(wait_until='domcontentloaded', timeout=60000):
                page.locator('#problem_submit input[type=submit]').click()
            match = re.fullmatch(r'/submission/(\d+)/?', urlparse(page.url).path)
            assert match, page.url
            sid = int(match.group(1))
            receipt = {'submission_id': sid, 'url': BASE + '/submission/' + str(sid), 'browser_form_post': posts[0],
                       'selected_language': label, 'reference_source_sha256': expected_sha}
            (OUT / 'submission-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
            assert len(posts) == 1 and posts[0]['source_canonical_sha256'] == expected_sha and posts[0]['language_id'] == language_id
        else:
            receipt = resume
            sid = receipt['submission_id']
            posts = [receipt['browser_form_post']]
            assert receipt['browser_form_post']['source_canonical_sha256'] == expected_sha
            receipt['reference_source_sha256'] = expected_sha
            (OUT / 'submission-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
            page.goto(BASE + '/submission/' + str(sid), wait_until='networkidle')
        if probe and probe['verdict'] == 'CE':
            page.wait_for_function("document.querySelector('#test-cases').textContent.includes('Compilation Error')", timeout=120000)
            assert page.locator('#test-cases .case-row').count() == 0
            statuses, labels = [], []
            assert page.locator('#test-cases pre').inner_text().strip()
        else:
            page.wait_for_function("document.querySelectorAll('#test-cases .case-row').length===103 && document.querySelector('#test-cases').textContent.includes('Final score:')", timeout=600000)
            rows = page.locator('#test-cases .case-row')
            statuses = [x.strip() for x in rows.locator('td:nth-child(2) span').all_text_contents()]
            expected_cases = probe['cases'] if probe else ['AC'] * 103
            assert statuses == expected_cases, statuses
            labels = [int(re.search(r'Test case #(\d+)', x).group(1)) for x in rows.locator('td:first-child').all_text_contents()]
            assert labels == list(range(1, 104))
            final = page.locator('#test-cases').inner_text()
            expected_score = probe['score'] if probe else '103/103'
            assert expected_score in final.replace(' ', '')
        page.screenshot(path=str(OUT / 'native-final-cases.png'), full_page=True)
        (OUT / 'native-final-status.html').write_text(page.content())
        page.goto(BASE + '/submissions/user/' + credentials['username'] + '/', wait_until='networkidle')
        row = page.locator('[id="' + str(sid) + '"].submission-row')
        assert row.count() == 1
        verdict = row.locator('.status').inner_text().strip()
        assert verdict == (probe['verdict'] if probe else 'AC')
        long_verdict = row.locator('.status').get_attribute('title')
        assert long_verdict == (probe['long_verdict'] if probe else 'Accepted')
        assert row.locator('.language').inner_text().strip() == 'C++23'
        list_score = row.locator('.score').inner_text().replace(' ', '').strip()
        if not probe or probe['verdict'] != 'CE':
            assert list_score == (probe['score'] if probe else '103/103')
        page.screenshot(path=str(OUT / 'native-submission-list.png'), full_page=True)
        (OUT / 'native-submission-list.html').write_text(page.content())
        assert polls and all(code==200 for code in polls), 'Authenticated live polling must update the native result'
        assert not errors, errors
        assert set(blocked) <= {'www.gravatar.com'}, blocked
        result = {'status': 'PASS', **receipt, 'displayed_verdict': verdict, 'displayed_long_verdict': long_verdict,
                  'displayed_case_count': len(statuses), 'displayed_cases': statuses, 'displayed_case_numbers': labels, 'displayed_score': list_score,
                  'actual_native_form_post_count': 0 if resume else len(posts), 'original_native_form_post_count': len(posts), 'read_only_resume': bool(resume), 'page_error_count': 0,
                  'blocked_decoration_hosts': sorted(set(blocked)), 'source_injected_only_into_native_Ace_form': True,
                  'authenticated_poll_responses':polls, 'contest_standings': 'NOT CLAIMED in checkpoint1 smoke'}
        (OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        page.goto(BASE + '/', wait_until='domcontentloaded')
        page.locator('#user-links > ul > li > a').hover()
        with page.expect_navigation(wait_until='domcontentloaded'):
            page.locator('form[action="/accounts/logout/"] button[type=submit]').click()
    finally:
        if not (OUT / 'submission-receipt.json').exists():
            (OUT / 'form-diagnostic.html').write_text(page.content())
            page.screenshot(path=str(OUT / 'form-diagnostic.png'), full_page=True)
        (OUT / 'sessions.json').write_text(json.dumps([c['value'] for c in context.cookies() if c['name'] == 'sessionid']))
        context.close(); browser.close()
print('PASS: genuine participant native browser POST and expected displayed verdict/cases.')
