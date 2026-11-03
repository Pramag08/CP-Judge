"""Bounded B01 follow-up operations; fresh evidence, no B01 report mutation."""
import argparse
import hashlib
import shutil
import time
import urllib.request
import datetime
import grp
import json
import os
from pathlib import Path
import shlex
import secrets
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
WORK=Path(os.environ.get('CPJ_FOLLOWUP_WORK',ROOT/'build/b01-followup-1'))
REPORT=Path(os.environ.get('CPJ_FOLLOWUP_REPORT',ROOT/'reports/b01-followup-1'))
SITE='cpjudge-b01-site'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['inspect','bundle','apply','diagnose','finish-assets','fixtures','browser','verify','check-changed','reset-fixtures','check-reset','cleanup','render-fixtures','refresh-preview','inspect-actions','refresh-admin','final-audit','refresh-math','fixtures-again','math-browser'])
    args=parser.parse_args()
    if grp.getgrnam('docker').gr_gid not in [os.getgid(),*os.getgroups()]:
        os.execvp('sg',['sg','docker','-c',shlex.join([sys.executable,'-B',str(Path(__file__).resolve()),args.action])])
    WORK.mkdir(exist_ok=True,parents=True)
    REPORT.mkdir(exist_ok=True,parents=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    raw=WORK/'logs'/stamp; raw.mkdir(parents=True)
    public=REPORT/'logs'/stamp; public.mkdir(parents=True)
    private=ROOT/'build/b01-site-1/private'
    secret_values=[]
    for path in private.glob('*.env'):
        secret_values.extend(line.split('=',1)[1] for line in path.read_text().splitlines() if '=' in line)
    accounts=private/'accounts.json'
    if accounts.exists():
        secret_values.extend(value for row in json.loads(accounts.read_text()).values() for value in row.values())
    fixture_file=WORK/'private/accounts.json'
    if fixture_file.exists():
        secret_values.extend(value for row in json.loads(fixture_file.read_text()).values() for value in row.values() if isinstance(value,str))
    def run(name,argv,stdin=None,public_log=True):
        print(name+': running',flush=True)
        proc=subprocess.run(argv,input=stdin,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (raw/(name+'.log')).write_text(proc.stdout);(raw/(name+'.log')).chmod(0o600)
        sanitized=proc.stdout
        for value in sorted(secret_values,key=len,reverse=True):
            if len(value)>=6:sanitized=sanitized.replace(value,'[REDACTED]')
        if public_log:(public/(name+'.log')).write_text(sanitized)
        file=REPORT/'commands.json';records=json.loads(file.read_text()) if file.exists() else []
        records.append({'action':args.action,'name':name,'argv':argv,'exit_status':proc.returncode,
                        'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'log':str(((public if public_log else raw)/(name+'.log')).relative_to(ROOT))})
        file.write_text(json.dumps(records,indent=2)+'\n')
        print(name+': exit '+str(proc.returncode),flush=True)
        if proc.returncode:raise RuntimeError(name+' failed; see fresh logs')
        return proc.stdout
    def shell(name,code):
        return run(name,['docker','exec','-i',SITE,'python','manage.py','shell'],code)
    if args.action=='refresh-math':
        for rel in ['templates/mathjax-load.html','templates/problem/raw.html']:
            source=HERE/'overlays'/rel
            shutil.copy2(source,WORK/'context/overlays'/rel)
            run('math-startup-'+source.name,['docker','cp',str(source),SITE+':/app/'+rel])
        run('refresh-math-thin-image',['docker','build','--progress=plain','-t','cpjudge-b01-site:followup1',str(WORK/'context')])
        return
    if args.action=='math-browser':
        output=WORK/'browser'/stamp;output.mkdir(parents=True)
        run('real-browser-math-final',['docker','run','--rm','--user',str(os.getuid())+':'+str(os.getgid()),
            '--network','host','--memory','1g','--cpus','2','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--mount',f'type=bind,src={fixture_file},dst=/run/accounts.json,readonly',
            '--mount',f'type=bind,src={HERE / "followup_math_browser.py"},dst=/tests/browser.py,readonly',
            '--mount',f'type=bind,src={output},dst=/results',
            'cpjudge-b01-browser:local1','python','/tests/browser.py'],public_log=False)
        result=json.loads((output/'result.json').read_text());result['private_artifacts']=str(output.relative_to(ROOT))
        (REPORT/('browser-math-final-'+stamp+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print('PASS: final visual/DOM math checks; exact equation counts, local extensions/fonts and zero page errors.')
        return
    if args.action=='final-audit':
        run('final-static-collection',['docker','exec',SITE,'python','manage.py','collectstatic','--noinput'])
        shell('unsilenced-system-warnings',"from django.test import override_settings\nfrom django.core.management import call_command\nwith override_settings(SILENCED_SYSTEM_CHECKS=[]):call_command('check',databases=['default'])\n")
        run('production-hardening-warnings',['docker','exec',SITE,'python','manage.py','check','--deploy'])
        code="""import hashlib,json
from pathlib import Path
from django.contrib.staticfiles import finders
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.apps import apps
from django.db import connection
loader=MigrationLoader(connection);loader.check_consistent_history(connection)
assert ('judge','0153_reconcile_model_metadata') in loader.applied_migrations
assert not MigrationAutodetector(loader.project_state(),ProjectState.from_apps(apps)).changes(graph=loader.graph)
assert not Path('/tmp/cpjudge-followup-state.json').exists()
assert not Path('/app/resources/cpjudge-fixtures/b01-followup-statement.html').exists()
paths={name:finders.find(name,all=True) for name in ['wpadmin/css/wpadmin.site.css','admin/js/jquery.init.js','cpjudge/wpadmin-site.css']}
assert all(len(v)==1 for v in paths.values())
assert Path(paths['admin/js/jquery.init.js'][0]).read_bytes()==Path('/app/static-followup/admin/js/jquery.init.js').read_bytes()
assert Path('/app/resources/martor-mathjax.js').read_bytes()==Path('/app/static-followup/martor-mathjax.js').read_bytes()
relative=['templates/admin/base_site.html','templates/mathjax-load.html','templates/problem/raw.html','resources/martor-mathjax.js']
math={str(p.relative_to('/app/resources/vendor/mathjax-3.2.2')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/resources/vendor/mathjax-3.2.2').rglob('*') if p.is_file()}
print(json.dumps({'applied_migrations':len(loader.applied_migrations),'migration_history_consistent':True,'autodetector_changes':{},
'migration_0153_sha256':hashlib.sha256(Path('/app/judge/migrations/0153_reconcile_model_metadata.py').read_bytes()).hexdigest(),
'runtime_overlay_sha256':{r:hashlib.sha256((Path('/app')/r).read_bytes()).hexdigest() for r in relative},
'math_files_sha256':math,'static_destinations':paths,'generated_js_catalogue_exists':Path('/app/static-followup/jsi18n/en/djangojs.js').exists(),
'collected_and_source_bootstrap_preview_equal':True,'temporary_fixtures_removed':True,'actual_import_judging_standings':'NOT TESTED'},indent=2))
"""
        output=shell('final-read-only-runtime-audit',code)
        result=json.loads(output[output.index('{'):])
        expected=json.loads((REPORT/'math-assets.json').read_text())['files_sha256']
        assert result['math_files_sha256']==expected
        for rel,digest in result['runtime_overlay_sha256'].items():assert hashlib.sha256((HERE/'overlays'/rel).read_bytes()).hexdigest()==digest
        baseline=json.loads((WORK/'before-files.json').read_text())
        assert result['migration_0153_sha256']==baseline['deploy/site-local/migrations/0153_reconcile_model_metadata.py']
        runtime=run('running-services',['docker','inspect','cpjudge-b01-site','cpjudge-b01-db','cpjudge-b01-redis','--format','{{.Name}} {{.State.Running}} {{json .NetworkSettings.Ports}}'])
        result['services_observed']=runtime.strip().splitlines()
        assert all(' true ' in row for row in result['services_observed'])
        with urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/',timeout=5) as r:assert r.status==200
        result.update({'status':'PASS','local_url':'http://127.0.0.1:8000/','host_login_http_status':200,'services_running':True})
        (REPORT/'runtime-final.json').write_text(json.dumps(result,indent=2)+'\n')
        print('PASS: source/assets/migrations match, fixtures removed, no destination conflicts; existing local services running.')
        return
    if args.action=='refresh-admin':
        shutil.copy2(HERE/'install_followup.py',WORK/'context/install_followup.py')
        run('admin-modern-api-installer',['docker','cp',str(HERE/'install_followup.py'),SITE+':/tmp/install_followup.py'])
        run('native-actions-initialization',['docker','exec','--user','root',SITE,'python','/tmp/install_followup.py','library'])
        code="""import os,signal
from pathlib import Path
found=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:args=(p/'cmdline').read_bytes().split(b'\\0')
  except (OSError,PermissionError):continue
  if len(args)>2 and args[1:3]==[b'manage.py',b'runserver']:
   found.append(int(p.name))
assert len(found)==1,found
os.kill(found[0],signal.SIGTERM)
print('Restarted only the matched development web process; containers/database/background services untouched.')
"""
        run('stop-web-process-only',['docker','exec','-i',SITE,'python'],code)
        run('restart-web-process',['docker','exec','-d',SITE,'sh','-c',
            'exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/b01-followup-http.log 2>&1'])
        for _ in range(30):
            try:
                with urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/',timeout=2) as r:
                    if r.status==200:break
            except Exception:time.sleep(1)
        else:raise RuntimeError('web not ready')
        run('refresh-admin-thin-image',['docker','build','--progress=plain','-t','cpjudge-b01-site:followup1',str(WORK/'context')])
        return
    if args.action=='inspect-actions':
        output=shell('native-admin-action-initializers',"from pathlib import Path\nimport wpadmin,django\nfor label,p in [('wpadmin',Path(wpadmin.__file__).parent/'templates/admin/change_list.html'),('django',Path(django.__file__).parent/'contrib/admin/templates/admin/change_list.html'),('actions',Path(django.__file__).parent/'contrib/admin/static/admin/js/actions.js')]:\n print('SOURCE',label,'\\n'+p.read_text())\n")
        print(output)
        return
    if args.action=='refresh-preview':
        source=HERE/'overlays/resources/martor-mathjax.js'
        shutil.copy2(source,WORK/'context/overlays/resources/martor-mathjax.js')
        run('preview-startup-promise',['docker','cp',str(source),SITE+':/app/resources/martor-mathjax.js'])
        run('refresh-thin-overlay-image',['docker','build','--progress=plain','-t','cpjudge-b01-site:followup1',str(WORK/'context')])
        return
    if args.action=='render-fixtures':
        output=shell('render-native-fixtures',"OP='render'\n"+(HERE/'followup_fixture.py').read_text())
        result=json.loads(output[output.index('{'):])
        credentials=json.loads(fixture_file.read_text())
        for role,pk in result['fixture_ids'].items():credentials[role]['id']=pk
        fixture_file.write_text(json.dumps(credentials,indent=2)+'\n')
        (REPORT/'fixture-scope.json').write_text(json.dumps(result,indent=2)+'\n')
        return
    if args.action in ['fixtures','fixtures-again']:
        if args.action=='fixtures-again' and fixture_file.exists():
            fixture_file.rename(fixture_file.with_name('accounts-'+stamp+'.json'))
        private_dir=WORK/'private';private_dir.mkdir(exist_ok=True,mode=0o700);private_dir.chmod(0o700)
        assert not fixture_file.exists(), 'fixture setup already exists'
        credentials={role:{'username':'fu-'+role+'-'+secrets.token_hex(5),
                            'password':secrets.token_urlsafe(24),'changed_password':secrets.token_urlsafe(24)}
                     for role in ['staff','participant']}
        fixture_file.write_text(json.dumps(credentials,indent=2)+'\n');fixture_file.chmod(0o600)
        secret_values.extend(value for row in credentials.values() for value in row.values())
        run('private-fixture-credentials',['docker','exec','-i',SITE,'python','-c',
            "import os,sys; fd=os.open('/tmp/cpjudge-followup-fixtures.json',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600); os.write(fd,sys.stdin.buffer.read()); os.close(fd)"],fixture_file.read_text())
        output=shell('temporary-math-auth-fixtures',"OP='setup'\n"+(HERE/'followup_fixture.py').read_text())
        result=json.loads(output[output.index('{'):])
        for role,pk in result['fixture_ids'].items():credentials[role]['id']=pk
        fixture_file.write_text(json.dumps(credentials,indent=2)+'\n')
        (REPORT/'fixture-scope.json').write_text(json.dumps(result,indent=2)+'\n')
        return
    if args.action in ['check-changed','check-reset','cleanup','render-fixtures','refresh-preview','inspect-actions','refresh-admin','final-audit','refresh-math','fixtures-again','math-browser']:
        op={'check-changed':'changed','check-reset':'reset','cleanup':'cleanup'}[args.action]
        output=shell('existing-accounts-and-'+op,"OP="+repr(op)+"\n"+(HERE/'followup_fixture.py').read_text())
        (REPORT/('accounts-'+op+'.json')).write_text(output[output.index('{'):])
        return
    if args.action=='verify':
        run('ordinary-verification',['env','CPJ_SITE_REPORT_DIR='+str(REPORT),sys.executable,'-B',str(HERE/'manage.py'),'verify'])
        return
    if args.action=='reset-fixtures':
        run('explicit-fixture-password-reset',['env','CPJ_SITE_REPORT_DIR='+str(REPORT),sys.executable,'-B',str(HERE/'manage.py'),
            'reset-accounts','--account-file',str(fixture_file)])
        return
    if args.action=='browser':
        previous=sorted(REPORT.glob('browser-change-*.json'))
        phase='change' if not previous else ('after-reset' if (REPORT/'accounts-reset.json').exists() else 'after-verify')
        output=WORK/'browser'/stamp;output.mkdir(parents=True)
        run('real-browser-'+phase,['docker','run','--rm','--user',str(os.getuid())+':'+str(os.getgid()),
            '--network','host','--memory','1g','--cpus','2','--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--env','B01_FU_PHASE='+phase,
            '--mount',f'type=bind,src={fixture_file},dst=/run/accounts.json,readonly',
            '--mount',f'type=bind,src={HERE / "followup_browser.py"},dst=/tests/browser.py,readonly',
            '--mount',f'type=bind,src={output},dst=/results',
            'cpjudge-b01-browser:local1','python','/tests/browser.py'],public_log=False)
        result=json.loads((output/'result.json').read_text())
        result['private_artifacts']=str(output.relative_to(ROOT))
        (REPORT/('browser-'+phase+'-'+stamp+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print('PASS: actual Chromium '+phase+' checks; private artifacts retained.')
        return
    if args.action=='finish-assets':
        run('compile-local-js-catalogue',['docker','exec',SITE,'python','manage.py','compilejsi18n'])
        with urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/',timeout=5) as r:assert r.status==200
        result=shell('single-static-destinations',"import json\nfrom django.contrib.staticfiles import finders\nfrom django.conf import settings\nrows={name:finders.find(name,all=True) for name in ['wpadmin/css/wpadmin.site.css','admin/js/jquery.init.js','cpjudge/wpadmin-site.css']}\nassert all(len(v)==1 for v in rows.values()),rows\nassert 'django/contrib/admin' in rows['admin/js/jquery.init.js'][0]\nprint(json.dumps({'static_candidates':rows,'static_root':settings.STATIC_ROOT,'finders':settings.STATICFILES_FINDERS},indent=2))\n")
        (REPORT/'static-resolution.json').write_text(result[result.index('{'):])
        print('PASS: regenerated JS catalogue in the fresh static root; local page HTTP 200 and canonical asset sources verified.')
        return
    if args.action=='diagnose':
        log=run('followup-web-log',['docker','exec',SITE,'cat','/tmp/b01-followup-http.log'],public_log=False)
        print(log[-9000:])
        return
    if args.action=='bundle':
        workspace=WORK/'npm'
        workspace.mkdir(exist_ok=True)
        for name in ['package.json','package-lock.json']:
            src=HERE/'assets'/name
            if src.exists():shutil.copy2(src,workspace/name)
        node=json.loads((ROOT/'reports/a09-site-1/base-pins.json').read_text())['node']
        command='npm ci --ignore-scripts'
        if not (workspace/'package-lock.json').exists():
            command='npm install --package-lock-only --ignore-scripts && '+command
        run('mathjax-locked-install',['docker','run','--rm','--user',str(os.getuid())+':'+str(os.getgid()),
            '--mount',f'type=bind,src={workspace},dst=/work','--workdir','/work',
            '--env','npm_config_cache=/tmp/npm-cache',node,'sh','-c',command])
        lock=workspace/'package-lock.json'
        target=HERE/'assets/package-lock.json'
        if target.exists():assert target.read_bytes()==lock.read_bytes()
        else:shutil.copy2(lock,target)
        package=workspace/'node_modules/mathjax'
        assert json.loads((package/'package.json').read_text())['version']=='3.2.2'
        context=WORK/'context'
        context.mkdir(exist_ok=False)
        shutil.copytree(HERE/'overlays',context/'overlays')
        (context/'mathjax').mkdir()
        shutil.copytree(package/'es5',context/'mathjax/es5')
        shutil.copy2(package/'LICENSE',context/'mathjax/LICENSE')
        for name in ['Dockerfile.followup','install_followup.py']:
            shutil.copy2(HERE/name,context/('Dockerfile' if name.startswith('Dockerfile') else name))
        entries={str(p.relative_to(context/'mathjax')):hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (context/'mathjax').rglob('*') if p.is_file()}
        (REPORT/'math-assets.json').write_text(json.dumps({'version':'3.2.2','node_image':node,
            'package_lock_sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),
            'npm_integrity':json.loads(lock.read_text())['packages']['node_modules/mathjax']['integrity'],
            'license':'Apache-2.0 (LICENSE retained)', 'files_sha256':entries},indent=2)+'\n')
        run('thin-overlay-image',['docker','build','--progress=plain','-t','cpjudge-b01-site:followup1',str(context)])
        print('Bundled pinned MathJax JS/extensions/fonts/license and built thin overlay image.')
        return
    if args.action=='apply':
        context=WORK/'context'
        assert (context/'mathjax/es5/tex-chtml.js').exists(), 'bundle first'
        before=WORK/'runtime-before'
        before.mkdir(exist_ok=False)
        # Refuse to overwrite unknown changes to these exact upstream files.
        for rel in [str(p.relative_to(HERE/'overlays')) for p in (HERE/'overlays').rglob('*') if p.is_file()]:
            path=before/rel;path.parent.mkdir(parents=True,exist_ok=True)
            run('save-'+path.name,['docker','cp',SITE+':/app/'+rel,str(path)])
            expected=ROOT/'build/a09-site-1/site'/rel
            assert path.read_bytes()==expected.read_bytes(), 'existing runtime edits require integration: '+rel
        run('save-current-settings',['docker','cp',SITE+':/app/dmoj/local_settings.py',str(before/'local_settings.py')],public_log=False)
        run('source-parent',['docker','exec',SITE,'python','-c',"from pathlib import Path; Path('/app/resources/vendor').mkdir(exist_ok=True)"])
        for p in (HERE/'overlays').rglob('*'):
            if p.is_file():run('install-'+p.name,['docker','cp',str(p),SITE+':/app/'+str(p.relative_to(HERE/'overlays'))])
        run('install-mathjax',['docker','cp',str(context/'mathjax'),SITE+':/app/resources/vendor/mathjax-3.2.2'])
        run('copy-installer',['docker','cp',str(HERE/'install_followup.py'),SITE+':/tmp/install_followup.py'])
        run('source-layout',['docker','exec',SITE,'python','/tmp/install_followup.py','source'])
        run('canonical-admin-bootstrap',['docker','exec','--user','root',SITE,'python','/tmp/install_followup.py','library'])
        run('compile-local-js-catalogue',['docker','exec',SITE,'python','manage.py','compilejsi18n'])
        run('collect-static-no-conflicts',['docker','exec',SITE,'python','manage.py','collectstatic','--noinput'])
        code="""import os,signal
from pathlib import Path
found=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:args=(p/'cmdline').read_bytes().split(b'\\0')
  except (OSError,PermissionError):continue
  if len(args)>2 and args[1:3]==[b'manage.py',b'runserver']:
   found.append(int(p.name))
assert len(found)==1,found
os.kill(found[0],signal.SIGTERM)
print('Restarted only the matched development web process; containers/database/background services untouched.')
"""
        run('stop-web-process-only',['docker','exec','-i',SITE,'python'],code)
        run('restart-web-process',['docker','exec','-d',SITE,'sh','-c',
            'exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/b01-followup-http.log 2>&1'])
        for _ in range(30):
            try:
                with urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/',timeout=2) as r:
                    if r.status==200:break
            except Exception:time.sleep(1)
        else:raise RuntimeError('web not ready')
        audit="""import hashlib,json
from pathlib import Path
from django.contrib.staticfiles import finders
from django.conf import settings
rows={name:finders.find(name,all=True) for name in ['wpadmin/css/wpadmin.site.css','admin/js/jquery.init.js','cpjudge/wpadmin-site.css']}
assert all(len(v)==1 for v in rows.values()),rows
assert 'django/contrib/admin' in rows['admin/js/jquery.init.js'][0]
print(json.dumps({'static_candidates':rows,'static_root':settings.STATIC_ROOT,'finders':settings.STATICFILES_FINDERS},indent=2))
"""
        result=shell('single-static-destinations',audit)
        (REPORT/'static-resolution.json').write_text(result[result.index('{'):])
        print('Applied overlay without replacing containers/database or rewriting migration history.')
        return
    if args.action=='inspect':
        run('existing-services',['docker','ps','-a','--format','{{.Names}} {{.Status}} {{.Image}}'])
        run('current-site-image',['docker','inspect',SITE,'--format','{{.Image}} {{json .NetworkSettings.Ports}}'])
        code='''import hashlib,json,importlib.metadata as m
from pathlib import Path
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.template import engines
from django.contrib.auth.models import User
from judge.models import Judge,RuntimeVersion
rows={}
for name in ['wpadmin/css/wpadmin.site.css','admin/js/jquery.init.js']:
 paths=finders.find(name,all=True)
 rows[name]=[{'path':p,'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest(),'content':Path(p).read_text()} for p in paths]
print(json.dumps({'duplicates':rows,'judge_rows':Judge.objects.count(),'runtime_rows':RuntimeVersion.objects.count(),'users':User.objects.count()},indent=2))
import wpadmin
root=Path(wpadmin.__file__).parent
print('WPADMIN',root)
for name in ['templates/admin/base.html','templates/admin/base_site.html']:
 p=root/name
 if p.exists():print('TEMPLATE',name,'\\n'+p.read_text())
'''
        result=shell('static-template-inspection',code)
        print(result)

if __name__=='__main__':main()
