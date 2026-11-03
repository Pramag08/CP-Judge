"""C12 actual Chromium re-upload and concurrent authenticated HTTP uploads."""
import http.client
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8000'
accounts = json.loads(Path('/run/accounts.json').read_text())['accounts']
result = {'status': 'PASS', 'published_job': 24, 'checks': {}}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    def login(role):
        context = browser.new_context()
        context.route('**/*', lambda r: r.continue_() if urlsplit(r.request.url).hostname == '127.0.0.1' else r.abort())
        page = context.new_page()
        page.goto(BASE + '/accounts/login/')
        page.locator('#id_username').fill(accounts[role]['username'])
        page.locator('#id_password').fill(accounts[role]['password'])
        page.locator('form.form-area button[type=submit]').click()
        page.wait_for_url('**/contests/')
        return context, page

    def reupload(page, contest, data):
        page.goto(BASE + f'/contest/{contest}/import/')
        page.locator('input[name=package]').set_input_files(
            {'name': 'renamed-package.zip', 'mimeType': 'application/zip', 'buffer': data})
        with page.expect_navigation(wait_until='domcontentloaded'):
            page.locator('form[enctype="multipart/form-data"] button[type=submit]').click()
        match = re.fullmatch(r'/imports/(\d+)/', urlsplit(page.url).path)
        assert match, page.url
        return int(match[1])

    author, page = login('a')
    page.goto(BASE + '/imports/24/')
    assert page.locator('#publication-state').inner_text() == 'published'
    code = page.locator('#published-version').inner_text()
    attempt = page.locator('#import-attempt').inner_text()
    response = author.request.get(BASE + '/imports/24/download/')
    assert response.status == 200
    published_data = response.body()
    assert reupload(page, 'c1livea', published_data) == 24
    page.reload()
    assert page.locator('#published-version').inner_text() == code
    assert page.locator('#import-attempt').inner_text() == attempt
    assert page.locator('#publication-state').inner_text() == 'published'
    result.update(native_code=code, attempt=int(attempt))
    result['checks']['published_browser_reupload_refresh_existing_version'] = True

    # Six actual HTTP requests, one current browser session, simultaneous send.
    data = Path('/run/race.zip').read_bytes()
    cookies = {c['name']: c['value'] for c in author.cookies()}
    barrier = Barrier(6)

    def concurrent_post(_):
        boundary = 'C12Boundary'
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="package"; filename="race.zip"\r\n'
                'Content-Type: application/zip\r\n\r\n').encode() + data + f'\r\n--{boundary}--\r\n'.encode()
        headers = {'Content-Type': f'multipart/form-data; boundary={boundary}',
                   'Cookie': '; '.join(f'{k}={v}' for k, v in cookies.items()),
                   'X-CSRFToken': cookies['csrftoken'], 'Referer': BASE + '/contest/c1livea/import/'}
        conn = http.client.HTTPConnection('127.0.0.1', 8000, timeout=60)
        try:
            barrier.wait(timeout=20)
            conn.request('POST', '/contest/c1livea/import/', body, headers)
            response = conn.getresponse()
            outcome = (response.status, response.getheader('Location'))
            response.read()
            return outcome
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(concurrent_post, range(6)))
    assert all(status == 302 for status, _ in responses), responses
    assert len({location for _, location in responses}) == 1, responses
    race_job = int(re.fullmatch(r'/imports/(\d+)/', responses[0][1])[1])
    result['race_job'] = race_job
    result['checks']['six_simultaneous_http_uploads_one_redirect'] = True

    other, other_page = login('b')
    for suffix in ('', 'download/'):
        assert other.request.get(BASE + '/imports/24/' + suffix).status == 404
    own_job = reupload(other_page, 'c1liveb', published_data)
    assert own_job != 24
    assert other_page.locator('#import-attempt').inner_text() == '0'
    assert other_page.locator('#published-version').count() == 0
    assert other_page.locator('#import-status').inner_text() == 'uploaded'
    response = other.request.get(BASE + f'/imports/{own_job}/download/')
    assert response.status == 200 and response.body() == published_data
    for context, job in ((author, own_job), (other, 24)):
        for suffix in ('', 'download/'):
            assert context.request.get(BASE + f'/imports/{job}/' + suffix).status == 404
    result['other_owner_job'] = own_job
    result['checks']['same_bytes_other_owner_independent_job_and_mutual_404'] = True
    page.goto(BASE + '/imports/24/')
    page.screenshot(path='/results/reupload.png', full_page=True)
    author.close()
    other.close()
    browser.close()

Path('/results/browser.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS: C12 published browser re-upload, six simultaneous HTTP uploads and owner isolation.')
