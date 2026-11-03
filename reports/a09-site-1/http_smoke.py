import os, json, re, hashlib
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import requests
BASE='http://127.0.0.1:8000'
class Assets(HTMLParser):
    def __init__(self): super().__init__(); self.urls=[]; self.external=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='script' and a.get('src'): self.urls.append(a['src'])
        if tag=='link' and a.get('rel')=='stylesheet': self.urls.append(a['href'])
def get(s,path,status=200):
    r=s.get(urljoin(BASE,path),timeout=15); assert r.status_code==status,(path,r.status_code); return r
s=requests.Session()
login=get(s,'/accounts/login/')
assert 'csrfmiddlewaretoken' in login.text
bad=s.post(BASE+'/accounts/login/',data={'username':'a09-smoke','password':'intentionally-invalid','csrfmiddlewaretoken':s.cookies['csrftoken'],'next':'/user'},headers={'Referer':BASE+'/accounts/login/'},timeout=15)
assert bad.status_code==200 and 'Invalid username or password' in bad.text
missing=requests.post(BASE+'/accounts/login/',data={'username':'a09-smoke','password':'invalid'},timeout=15)
assert missing.status_code==403
p=Assets();p.feed(login.text)
local=sorted({u for u in p.urls if urlparse(urljoin(BASE,u)).netloc=='127.0.0.1:8000'})
external=sorted(set(p.urls)-set(local))
extra=['/static/a09/ace/ace.js','/static/a09/ace/mode-c_cpp.js','/static/libs/fontawesome/fontawesome-webfont.woff2','/static/style.css','/static/dark/style.css','/static/libs/select2/select2.js']
results=[]
for path in sorted(set(local+extra)):
    a=get(s,path); assert len(a.content)>0
    assert not a.headers.get('Content-Type','').startswith('text/html'),path
    results.append({'path':path,'status':a.status_code,'type':a.headers.get('Content-Type'),'bytes':len(a.content),'sha256':hashlib.sha256(a.content).hexdigest()})
okay=s.post(BASE+'/accounts/login/',data={'username':'a09-smoke','password':os.environ['A09_LOGIN_PASSWORD'],'csrfmiddlewaretoken':s.cookies['csrftoken'],'next':'/user'},headers={'Referer':BASE+'/accounts/login/'},allow_redirects=False,timeout=20)
assert okay.status_code==302,(okay.status_code,okay.headers.get('Location'))
profile=get(s,okay.headers['Location']); assert 'a09-smoke' in profile.text
assert not urlparse(profile.url).path.startswith('/accounts/login')
again=s.get(BASE+'/accounts/login/',allow_redirects=False,timeout=15); assert again.status_code==302
home=get(s,'/')
get(s,'/problems/'); get(s,'/contests/'); get(s,'/status/'); runtime=get(s,'/runtimes/'); assert 'GNU C++23' not in runtime.text, 'offline executor must not be advertised as available'
print(json.dumps({'login_get':login.status_code,'invalid_password':bad.status_code,'csrf_required':missing.status_code,'valid_login':okay.status_code,'authenticated_profile':profile.status_code,'already_authenticated_redirect':again.status_code,'home':home.status_code,'offline_cpp23_hidden':True,'local_assets':results,'external_asset_urls':external,'javascript_execution':'NOT TESTED','judge_dispatch':'NOT TESTED'},indent=2))
