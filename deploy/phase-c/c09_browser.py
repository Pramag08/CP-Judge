"""Actual C09 Chromium rendering, raw-response and request-attempt checks."""
import io,json,re,time,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as etree
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000';OUT=Path('/results')
accounts=json.loads(Path('/run/accounts.json').read_text())['accounts']
result={'status':'PASS','checks':{},'jobs':{},'external_fixture_attempts':[]}
with zipfile.ZipFile('/run/real.zip') as z:
 names=[n for n in z.namelist() if n.startswith('statements/') and n.endswith('.html')];assert len(names)==1
 real=z.read(names[0]);body=re.split(r'<body[^>]*>',real.decode(),flags=re.I)[1].split('</BODY>')[0];real_math=re.findall(r'\$\$\$(.*?)\$\$\$',body,re.S)
 assert len(real_math)==30
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 def login(role):
  c=browser.new_context(viewport={'width':1440,'height':1000})
  attempts=[];c.on('request',lambda r:attempts.append(r.url))
  # An attempted blocked request still fails the fixture check below.
  c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
  page=c.new_page();a=accounts[role];page.goto(BASE+'/accounts/login/')
  page.locator('#id_username').fill(a['username']);page.locator('#id_password').fill(a['password']);page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/')
  return c,page,attempts
 author,page,attempts=login('a')
 cdp=author.new_cdp_session(page);cdp.send('Network.enable');cdp_requests=[]
 cdp.on('Network.requestWillBeSent',lambda e:cdp_requests.append(e['request']['url']))
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def upload(mode):
  buffer=io.BytesIO()
  image=Path('/run/image.png').read_bytes()
  hostile='''<div class="problem-statement"><p>Readable malicious fixture $$$\\frac{a}{b}$$$</p><pre><div>1 2</div><div>3</div></pre>
<script>window.c09Injected=1;fetch('https://c09-evil.invalid/script')</script>
<iframe src="https://c09-evil.invalid/frame"></iframe><svg onload="window.c09Injected=1"><image href="https://c09-evil.invalid/svg"/></svg>
<link rel="stylesheet" href="https://c09-evil.invalid/css"><style>@import 'https://c09-evil.invalid/import';p{background:url('https://c09-evil.invalid/background')}</style>
<p style="background-image:url(https://c09-evil.invalid/inline)" onclick="window.c09Injected=1">Click fixture</p>
<a href="javascript:window.c09Injected=1">Link text</a><img src="image.png" onload="window.c09Injected=1" onerror="window.c09Injected=1"><object data="https://c09-evil.invalid/object"></object></div>'''
  if mode=='real-statement':statement=real
  elif mode=='malicious':statement=hostile.encode()
  elif mode=='spoof':statement=b'<p>Do not show partial statement</p><img src="image.png">';image=b'<svg onload="window.c09Injected=1"><script>fetch("https://c09-evil.invalid/spoof")</script></svg>'
  elif mode=='external':statement=b'<p>Do not show partial statement</p><img src="https://c09-evil.invalid/direct">'
  else:statement=b'<p>$$$\\href{https://c09-evil.invalid/math}{x}$$$</p>'
  with zipfile.ZipFile('/run/package.zip') as src,zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as dst:
   xml=src.read('problem.xml')
   doc=etree.fromstring(xml);decl=doc.find('statements/statement');assert decl is not None
   statement_path=decl.get('path');assert statement_path.startswith('statements/')
   for info in src.infolist():
    if info.filename==statement_path:data=statement
    elif info.filename=='problem.xml':data=etree.tostring(doc)
    else:data=src.read(info.filename)
    dst.writestr(info,data)
   dst.writestr(str(Path(statement_path).parent/'image.png'),image)
   dst.comment=('C09-'+mode+'-1').encode()
  page.goto(BASE+'/contest/c1livea/import/')
  page.locator('input[name=package]').set_input_files({'name':'c09-'+mode+'.zip','mimeType':'application/zip','buffer':buffer.getvalue()})
  with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form[enctype="multipart/form-data"] button').click()
  job=int(re.fullmatch(r'/imports/(\d+)/',urlsplit(page.url).path)[1]);result['jobs'][mode]=job
  if page.locator('#import-status').inner_text()=='uploaded':
   with page.expect_navigation(wait_until='domcontentloaded'):page.locator('form[action$="/convert/"] button').click()
  for _ in range(300):
   status=page.locator('#import-status').inner_text()
   if status in ('succeeded','failed'):break
   page.wait_for_timeout(250);page.reload()
  assert status=='succeeded',(mode,status)
  page.locator('#statement-preview-link').click();page.wait_for_load_state('networkidle')
  assert page.locator('#statement-attempt').inner_text()=='1'
  return job
 for mode in ('real-statement','malicious','spoof','external','unsafe-math'):
  job=upload(mode);url=page.url
  raw=author.request.get(url);assert raw.status==200
  assert raw.headers['cache-control']=='private, no-store' and raw.headers['x-content-type-options']=='nosniff'
  sub=page.evaluate('''text=>{let doc=new DOMParser().parseFromString(text,'text/html'),e=doc.querySelector('#statement-preview');return e?{bad:!!e.querySelector('script,style,link,svg,iframe,object,[style],[href],[onclick],[onload],[onerror]'),html:e.innerHTML}:null}''',raw.text())
  if mode in ('real-statement','malicious'):
   assert sub and not sub['bad']
   assert 'c09-evil.invalid' not in sub['html']
   page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise');page.evaluate('MathJax.startup.promise')
   assert page.locator('#statement-preview mjx-merror').count()==0
   observed=page.evaluate('Array.from(MathJax.startup.document.math).map(x=>x.math)')
   assert observed==(real_math if mode=='real-statement' else [r'\frac{a}{b}']),observed
   assert page.locator('.statement-notice').count()>0
   if mode=='real-statement':
    comparison=page.evaluate(r'''source=>{
     const doc=new DOMParser().parseFromString(source,'text/html');const norm=s=>s.replace(/\s+/g,' ').trim();let result={};
     for(const cls of ['legend','input-specification','output-specification','note']){
      let expected=doc.querySelector('.'+cls).textContent.replace(/\$\$\$(.*?)\$\$\$/gs,' MATH ');
      let actual=document.querySelector('#statement-preview .'+cls).cloneNode(true);actual.querySelectorAll('mjx-container').forEach(e=>e.replaceWith(' MATH '));result[cls]=norm(expected)===norm(actual.textContent);
     }
     for(const cls of ['input','output']){
      let pre=doc.querySelector('.sample-test .'+cls+' pre'),lines=[...pre.querySelectorAll(':scope > div')];let expected=lines.length?lines.map(e=>e.textContent).join('\n'):pre.textContent;
      result[cls]=norm(expected)===norm(document.querySelector('#statement-preview .sample-test .'+cls+' pre').textContent);
     }return result;
    }''',real.decode())
    assert all(comparison.values()),comparison
    result['checks']['real_unchanged_statement_30_equations_sections_samples']=True
   else:
    assert page.locator('#statement-preview pre').inner_text()=='1 2\n3\n'
    page.locator('#statement-preview p').last.click();assert page.evaluate('window.c09Injected') is None
    images=page.locator('#statement-preview img');assert images.count()==1
    assert images.first.evaluate('(e)=>e.complete && e.naturalWidth>0')
    asset=images.first.get_attribute('src');result['asset_path']=asset
    response=author.request.get(BASE+asset);assert response.status==200
    assert response.headers['content-type']=='image/png' and response.headers['x-content-type-options']=='nosniff' and response.headers['cache-control']=='private, no-store'
    assert response.body().startswith(b'\x89PNG\r\n\x1a\n')
    result['checks']['malicious_markup_removed_real_png_loaded']=True
  else:
   assert not sub and page.locator('#statement-preview').count()==0
   assert 'Statement preview unavailable' in page.locator('.statement-notice').inner_text()
  for _ in range(2):
   page.reload();page.wait_for_load_state('networkidle');assert page.locator('#statement-attempt').inner_text()=='1'
   assert page.evaluate('window.c09Injected') is None
  page.screenshot(path=str(OUT/(mode+'.png')),full_page=True)
 assert not [u for u in attempts+cdp_requests if 'c09-evil.invalid' in u]
 result['checks']['zero_fixture_external_attempts_playwright_and_cdp']=True
 result['checks']['raw_response_sanitized_before_browser_or_request_blocking']=True
 result['legacy_external_hosts']=sorted({urlsplit(u).hostname for u in attempts if urlsplit(u).hostname!='127.0.0.1'})
 result['checks']['spoof_external_unsafe_math_no_partial_preview']=True
 asset=result['asset_path'];job=result['jobs']['malicious']
 for role in ('b','p',None):
  if role:c,other,_=login(role)
  else:c=browser.new_context();other=c.new_page()
  for path in (f'/imports/{job}/statement/',asset):assert other.goto(BASE+path).status in (401,403,404)
  c.close()
 for suffix in ('../problem.xml','%2e%2e%2fproblem.xml','%252e%252e%252fproblem.xml','checker.cpp','data.zip','testlib.h','reference.cpp','uploaded-package.zip','image.png','tests/001.a'):
  assert author.request.get(BASE+asset.rsplit('/',1)[0]+'/'+suffix).status in (400,401,403,404)
 assert author.request.get(BASE+asset.replace('/1/assets/','/2/assets/')).status==404
 other_job=result['jobs']['real-statement']
 assert author.request.get(BASE+asset.replace(f'/imports/{job}/',f'/imports/{other_job}/')).status==404
 result['checks']['direct_role_traversal_cross_import_and_attempt_denials']=True
 result['page_errors']=errors;assert not errors
 (OUT/'browser.json').write_text(json.dumps(result,indent=2)+'\n')
 author.close();browser.close()
print('PASS: C09 Chromium render, raw sanitized response, request attempts and direct-route isolation.')
