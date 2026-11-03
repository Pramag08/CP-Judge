"""Actual local-browser and HTTP checks for the C05 single-ZIP route."""
import http.client,json,re,zipfile,io
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000'
accounts=json.loads(Path('/run/accounts.json').read_text())['accounts']
checks={}
blocked=[]

def package_bytes():
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  info=zipfile.ZipInfo('package-info.txt',(2020,1,1,0,0,0))
  z.writestr(info,'C05 browser upload fixture')
 return out.getvalue()

def cookies(context):
 return {x['name']:x['value'] for x in context.cookies()}

def raw_request(context,path,parts,*,token='valid',auth=True,chunked=False,unframed=False,declared=None):
 boundary='----CPJ-C05-browser-boundary'
 body=bytearray()
 for name,value in parts:
  body.extend(f'--{boundary}\r\n'.encode())
  if isinstance(value,tuple):
   filename,data=value
   body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\nContent-Type: application/zip\r\n\r\n'.encode())
   body.extend(data);body.extend(b'\r\n')
  else:
   body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
 body.extend(f'--{boundary}--\r\n'.encode())
 state=cookies(context) if context else {}
 headers={'Host':'127.0.0.1:8000','Content-Type':f'multipart/form-data; boundary={boundary}','Connection':'close'}
 if auth:
  headers['Cookie']='; '.join(f'{k}={v}' for k,v in state.items() if k in ('sessionid','csrftoken'))
  headers['Referer']=BASE+'/contest/c1livea/import/'
 if token=='valid':headers['X-CSRFToken']=state.get('csrftoken','')
 elif token=='invalid':headers['X-CSRFToken']='invalid-csrf-token'
 if not chunked and not unframed:headers['Content-Length']=str(declared if declared is not None else len(body))
 conn=http.client.HTTPConnection('127.0.0.1',8000,timeout=30)
 conn.putrequest('POST',path,skip_host=True)
 for key,value in headers.items():conn.putheader(key,value)
 conn.endheaders()
 if chunked:
  chunk=bytes(body)
  conn.send(f'{len(chunk):X}\r\n'.encode()+chunk+b'\r\n0\r\n\r\n')
 elif not unframed and (declared is None or declared==len(body)):
  conn.send(bytes(body))
 response=conn.getresponse();status=response.status;content=response.read();conn.close()
 return status,content

with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 def new_context():
  c=browser.new_context()
  c.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else (blocked.append(urlsplit(r.request.url).hostname),r.abort())[1])
  return c
 def login(role):
  c=new_context();page=c.new_page();credential=accounts[role]
  page.goto(BASE+'/accounts/login/');page.locator('#id_username').fill(credential['username']);page.locator('#id_password').fill(credential['password'])
  page.locator('form.form-area button[type=submit]').click();page.wait_for_url('**/contests/')
  return c,page

 author,page=login('a')
 page.goto(BASE+'/contest/c1livea/import/')
 assert page.title() and '32 MiB' in page.locator('#content-body').inner_text()
 assert page.locator('input[type=file][name=package]').count()==1
 data=package_bytes()
 page.locator('input[type=file][name=package]').set_input_files({'name':'browser-package.zip','mimeType':'application/zip','buffer':data})
 with page.expect_navigation(wait_until='domcontentloaded'):
  page.locator('form[enctype="multipart/form-data"] button[type=submit]').click()
 match=re.fullmatch(r'/imports/(\d+)/',urlsplit(page.url).path);assert match
 job_id=int(match.group(1))
 page_text=page.locator('#content-body').inner_text()
 assert 'ZIP upload received' in page_text and 'uploaded' in page_text.lower()
 assert 'No conversion, publication, or execution was started.' in page_text
 page.reload();assert 'ZIP upload received' in page.locator('#content-body').inner_text()
 download=author.request.get(BASE+f'/imports/{job_id}/download/')
 assert download.status==200 and download.body()==data
 assert 'attachment' in download.headers.get('content-disposition','').lower()
 checks['author_upload_confirm_refresh_download']='PASS'

 # Both absent and invalid CSRF tokens must fail even with a valid active session.
 file_payload={'name':'csrf.zip','mimeType':'application/zip','buffer':data}
 status=author.request.post(BASE+'/contest/c1livea/import/',multipart={'package':file_payload}).status
 assert status==403,status
 status=author.request.post(BASE+'/contest/c1livea/import/',headers={'X-CSRFToken':'invalid-csrf-token'},
      multipart={'csrfmiddlewaretoken':'invalid-csrf-token','package':file_payload}).status
 assert status==403,status
 checks['missing_and_invalid_csrf']='PASS'

 # Useful request errors; none of these invokes conversion or creates a record.
 status,body=raw_request(author,'/contest/c1livea/import/',[('csrfmiddlewaretoken',cookies(author).get('csrftoken',''))])
 assert status==400 and b'Choose one ZIP file' in body
 status,body=raw_request(author,'/contest/c1livea/import/',[('csrfmiddlewaretoken',cookies(author).get('csrftoken','')),('package',('bad.txt',b'no'))])
 assert status==400 and b'Polygon .zip' in body
 status,body=raw_request(author,'/contest/c1livea/import/',[('csrfmiddlewaretoken',cookies(author).get('csrftoken','')),('package',('bad.zip',b'not zip'))])
 assert status==400 and b'Invalid ZIP' in body
 status,body=raw_request(author,'/contest/c1livea/import/',[('csrfmiddlewaretoken',cookies(author).get('csrftoken','')),('package',('one.zip',data)),('package',('two.zip',data))])
 assert status==400 and b'exactly one ZIP' in body
 checks['missing_invalid_malformed_and_multiple_files']='PASS'

 # The server rejects an oversized declared body before persisting or reading it.
 limit=32*1024**2
 status,_=raw_request(author,'/contest/c1livea/import/',[],declared=limit+65537)
 assert status==413,status
 # The local WSGI server fails closed for transfer encoding it cannot delimit.
 status,_=raw_request(author,'/contest/c1livea/import/',[('csrfmiddlewaretoken',cookies(author).get('csrftoken',''))],chunked=True)
 assert status in (400,411,413),status
 chunked_status=status
 unframed_status,_=raw_request(author,'/contest/c1livea/import/',[],unframed=True)
 assert unframed_status==411,unframed_status
 checks['oversized_declared_and_untrusted_stream']='PASS'
 checks['observed_upload_statuses']={'declared_oversize':413,'chunked_without_content_length':chunked_status,'unframed_without_content_length':unframed_status}

 # Anonymous, participant, unrelated author and unscoped administrator boundaries.
 anonymous=new_context()
 assert anonymous.request.get(BASE+'/contest/c1livea/import/').status==401
 assert raw_request(None,'/contest/c1livea/import/',[('package',('x.zip',data))],auth=False)[0]==401
 participant,_=login('p')
 assert participant.request.get(BASE+'/contest/c1livea/import/').status==404
 assert raw_request(participant,'/contest/c1livea/import/',[('package',('x.zip',data))])[0]==404
 other,_=login('b')
 assert other.request.get(BASE+'/contest/c1livea/import/').status==404
 assert other.request.get(BASE+f'/imports/{job_id}/').status==404
 assert other.request.get(BASE+f'/imports/{job_id}/download/').status==404
 checks['anonymous_participant_cross_contest_author_denials']='PASS'

 # Static/media paths do not map to the separately stored private ZIP.
 for path in ('/media/private-cpj-imports/'+str(job_id)+'.zip','/static/private-cpj-imports/'+str(job_id)+'.zip'):
  assert author.request.get(BASE+path).status==404
 checks['public_static_media_denied']='PASS'
 for context in (author,anonymous,participant,other):context.close()
 browser.close()

Path('/results/browser.json').write_text(json.dumps({'status':'PASS','live_url':BASE,'accepted_job_id':job_id,'configured_limit_bytes':limit,'checks':checks,'external_hosts_blocked':sorted(set(blocked))},indent=2)+'\n')
print('PASS: C05 author browser upload and live HTTP boundary checks.')
