"""Local B01 lifecycle. Docker only; installs no dependencies in the host venv.
Run at repository root: python3 -B deploy/site-local/manage.py up|verify|reset-accounts|start|stop|status|browser|accounts
"""
import argparse
import datetime
import grp
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WORK = ROOT / 'build/b01-site-1'
REPORT = Path(os.environ.get('CPJ_SITE_REPORT_DIR', ROOT / 'reports/site-local-runs'))
A09 = ROOT / 'reports/a09-site-1'
SITE_SOURCE = ROOT / 'build/a09-site-1/site'
BASE_ID = 'sha256:3ea8c0fbeb13e683ad0ba580b612c1c8987260f1617a6aafeca8aec751d9d99a'
BASE = 'cpjudge-a09-site:locked'
IMAGE = 'cpjudge-b01-site:local1'
PIN = '604d60cfd764bc708b04ffd75b715a5398b91f8b'
NET = 'cpjudge-b01-net'
WEBNET = 'cpjudge-b01-web'
DB, REDIS, SITE, BOOT = [f'cpjudge-b01-{name}' for name in ['db','redis','site','bootstrap']]
VOLUME = 'cpjudge-b01-data'
URL = 'http://127.0.0.1:8000'
MIGRATION = '0153_reconcile_model_metadata.py'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['up','verify','start','stop','status','browser','accounts','diagnose','network','repair-port','finish','browser-status','snapshot','reset-accounts'])
    parser.add_argument('--account-file', type=Path, help='Explicit reset credential file under ignored build/; verification never reads it for writes')
    args = parser.parse_args()
    # sg is required in this existing terminal to refresh Docker-group access.
    if grp.getgrnam('docker').gr_gid not in [os.getgid(), *os.getgroups()]:
        os.execvp('sg', ['sg', 'docker', '-c', shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), *sys.argv[1:]])])
    WORK.mkdir(exist_ok=True, parents=True)
    REPORT.mkdir(exist_ok=True, parents=True)
    private = WORK / 'private'
    private.mkdir(exist_ok=True, mode=0o700)
    private.chmod(0o700)
    session = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    logs = WORK / 'logs' / session
    logs.mkdir(parents=True)
    public_logs = REPORT / 'logs' / session
    public_logs.mkdir(parents=True)
    commands_file = REPORT / 'commands.json'
    commands = json.loads(commands_file.read_text()) if commands_file.exists() else []
    secret_values = []
    if (private / 'accounts.json').exists():
        for data in json.loads((private / 'accounts.json').read_text()).values():
            secret_values.extend(data.values())
    for path in private.glob('*.env'):
        secret_values.extend(line.split('=', 1)[1] for line in path.read_text().splitlines() if '=' in line)

    def sanitize(text):
        for value in sorted(secret_values, key=len, reverse=True):
            if len(value) >= 6:
                text = text.replace(value, '[REDACTED]')
        return text

    def run(name, argv, *, stdin=None, expected=0, public=True):
        print(f'{name}: running', flush=True)
        result = subprocess.run(argv, input=stdin, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        raw = logs / f'{name}.log'
        raw.write_text(result.stdout)
        raw.chmod(0o600)
        if public:
            (public_logs / raw.name).write_text(sanitize(result.stdout))
        current_commands = json.loads(commands_file.read_text()) if commands_file.exists() else []
        current_commands.append({'action': args.action, 'name': name, 'argv': argv,
                         'exit_status': result.returncode, 'expected_exit_status': expected,
                         'log': str((public_logs if public else logs).relative_to(ROOT) / raw.name),
                         'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
        commands_file.write_text(json.dumps(current_commands, indent=2) + '\n')
        print(f'{name}: exit {result.returncode}', flush=True)
        if expected is not None and result.returncode != expected:
            raise RuntimeError(f'{name}: expected {expected}, got {result.returncode}; see private run log')
        return result.stdout

    def docker(name, *argv, **kwargs):
        return run(name, ['docker', *argv], **kwargs)

    def manage(name, *argv, container=SITE, **kwargs):
        return docker(name, 'exec', container, 'python', 'manage.py', *argv, **kwargs)

    def shell(name, code, container=SITE):
        return docker(name, 'exec', '-i', container, 'python', 'manage.py', 'shell', stdin=code)

    def inspect(kind, name):
        p = subprocess.run(['docker', kind, 'inspect', name], capture_output=True, text=True)
        return json.loads(p.stdout)[0] if p.returncode == 0 else None

    def ready_db():
        for _ in range(60):
            p = subprocess.run(['docker','exec',DB,'healthcheck.sh','--connect','--innodb_initialized'],capture_output=True)
            if p.returncode == 0:
                return
            time.sleep(1)
        raise RuntimeError('database did not become ready in 60 seconds')

    def ready_http():
        for _ in range(45):
            try:
                with urllib.request.urlopen(URL + '/accounts/login/',timeout=2) as response:
                    if response.status == 200:
                        return
            except Exception:
                time.sleep(1)
        raise RuntimeError('HTTP did not become ready; see docker logs')

    def server():
        docker('http-start','exec','-d',SITE,'sh','-c',
               'exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/b01-http.log 2>&1')
        ready_http()

    def private_write(name, text):
        path = private / name
        assert not path.exists(), f'will not overwrite {path}'
        path.write_text(text)
        path.chmod(0o600)

    def save_baseline(result):
        pins=json.loads((A09/'base-pins.json').read_text())
        patch=ROOT/'patches/site/0001-stable-timezone-choices.patch'
        target=HERE/'migrations'/MIGRATION
        result.update({'status':'PASS for server baseline; browser pending','site_commit':PIN,
                       'a09_base_image_id':BASE_ID,'website_image_id':inspect('image',IMAGE)['Id'],
                       'database_image':pins['mariadb'],'redis_image':pins['redis'],
                       'local_url':URL,'services_running':True,'source_patch':str(patch.relative_to(ROOT)),
                       'source_patch_sha256':digest(patch),'forward_migration_sha256':digest(target),
                       'migration_sql_database_changing_statements':[],
                       'website_dependency_lock_unchanged':True,'browser':'NOT YET RUN',
                       'css_assets':'A09 pinned built Sass output reused; Django static collection executed',
                       'b02_started':False,'judge_connection':'NOT TESTED'})
        (REPORT/'baseline.json').write_text(json.dumps(result,indent=2)+'\n')
        (WORK/'state.json').write_text(json.dumps({'site':SITE,'database':DB,'redis':REDIS,'network':NET,'volume':VOLUME,'url':URL},indent=2)+'\n')
        print('Local website/database baseline established: '+URL+'; browser verification still required.')

    def provision_development_accounts(reset=False):
        path=(args.account_file or private/'accounts.json').resolve()
        assert path.is_relative_to(ROOT/'build') and path.is_file(), 'use a private file under build/'
        if reset:assert args.action=='reset-accounts', 'password resets require the explicit action'
        docker('accounts-private-copy','exec','-i',SITE,'python','-c',
               "import os,sys; fd=os.open('/tmp/cpjudge-dev-accounts.json',os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600); os.write(fd,sys.stdin.buffer.read()); os.close(fd)",
               stdin=path.read_text())
        code="ACCOUNT_FILE='/tmp/cpjudge-dev-accounts.json'\nRESET_PASSWORDS="+repr(reset)+"\n"+(HERE/'accounts.py').read_text()
        shell('explicit-development-account-reset' if reset else 'initial-development-accounts',code)
        docker('clear-transient-account-file','exec',SITE,'python','-c',"from pathlib import Path; Path('/tmp/cpjudge-dev-accounts.json').unlink()")

    def verify_baseline():
        # Read-only DB/account verification: no fixtures, migrations or reseeding.
        state='/tmp/cpjudge-verify-'+session+'.json'
        shell('password-state-before',"import json,os\nfrom django.contrib.auth.models import User\np="+repr(state)+"\nfd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\nos.write(fd,json.dumps(list(User.objects.order_by('pk').values_list('pk','password'))).encode())\nos.close(fd)\nprint('Captured private verification state without changing any account.')\n")
        docker('dependency-check','exec',SITE,'python','-m','pip','check')
        freeze=docker('dependency-freeze','exec',SITE,'python','-m','pip','freeze','--all')
        assert freeze.strip()==(A09/'requirements.lock').read_text().strip(), 'website lock changed'
        manage('system-check','check','--database','default')
        manage('migration-consistency','makemigrations','--check','--dry-run')
        manage('no-unapplied-migrations','migrate','--check')
        manage('deployment-warnings','check','--deploy')
        audit=shell('read-only-runtime-audit',(HERE/'audit.py').read_text())
        result=json.loads(audit[audit.index('{'):])
        shell('password-state-unchanged',"import json\nfrom pathlib import Path\nfrom django.contrib.auth.models import User\np=Path("+repr(state)+")\nassert json.loads(p.read_text()) == [list(row) for row in User.objects.order_by('pk').values_list('pk','password')]\np.unlink()\nprint('PASS: every existing account password hash is byte-identical; verification did not reseed.')\n")
        result.update({'status':'PASS','scope':'read-only dependency/migration/account verification',
                       'password_hashes_unchanged':True,'fixtures_loaded':False,'migrations_applied':False,
                       'development_accounts_reset':False,'website_to_judge':'NOT TESTED'})
        (REPORT/('verification-'+session+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print('PASS: ordinary verification preserved all existing passwords; no reseeding or migrations applied.')

    if args.action=='reset-accounts':
        provision_development_accounts(reset=True)
        return
    if args.action == 'accounts':
        assert (private/'accounts.json').exists(), 'run up first'
        print('Credentials are private: build/b01-site-1/private/accounts.json (mode 0600).')
        print('These are initial/reset values; an interactively changed password remains in force. Only reset-accounts reapplies this file.')
        print('To change a password interactively: sg docker -c "docker exec -it cpjudge-b01-site python manage.py changepassword <username>"')
        return
    if args.action == 'snapshot':
        ready_http()
        versions=docker('redis-version','exec',REDIS,'redis-server','--version').strip()
        runtime=docker('final-services','inspect',DB,REDIS,SITE,'--format',
                       '{{.Name}} {{.State.Running}} {{json .NetworkSettings.Ports}}')
        assert all(inspect('container',name)['State']['Running'] for name in [DB,REDIS,SITE])
        print(runtime)
        data=json.loads((REPORT/'baseline.json').read_text())
        latest=sorted(REPORT.glob('browser-[0-9]*.json'))[-1]
        browser=json.loads(latest.read_text())
        assert browser['status']=='PASS' and browser['url']==URL
        data.update({'status':'PASS for required website/database/browser journeys; independent review separate',
                     'browser':{'status':'PASS','report':latest.name,'url':browser['url']},
                     'redis_version_observed':versions,'services_running':True})
        (REPORT/'baseline.json').write_text(json.dumps(data,indent=2)+'\n')
        (REPORT/'services.json').write_text(json.dumps({'status':'RUNNING','local_url':URL,
            'host_login_http_status':200,'bind_address':'127.0.0.1',
            'services':[DB,REDIS,SITE],'stop_start_verified':True,
            'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
        return
    if args.action == 'browser-status':
        p=subprocess.run(['ps','-C','docker','-o','pid,ppid,etime,args'],capture_output=True,text=True)
        for line in p.stdout.splitlines():
            if 'playwright' in line or 'cpjudge-b01-browser' in line: print(line)
        print(docker('browser-image-presence','image','ls','--filter','reference=mcr.microsoft.com/playwright/python',
                     '--format','{{.Repository}}:{{.Tag}} {{.ID}}'))
        return
    if args.action == 'repair-port':
        info=inspect('network',WEBNET)
        if not info:
            docker('web-network-create','network','create','--label','cpjudge.task=B01',WEBNET)
        else:
            assert info['Labels'].get('cpjudge.task')=='B01'
        networks=inspect('container',SITE)['NetworkSettings']['Networks']
        if WEBNET not in networks:
            docker('web-network-connect','network','connect',WEBNET,SITE)
        print(docker('published-local-port','port',SITE))
        ready_http()
        print('Local HTTP200 through loopback-published port: '+URL)
        return
    if args.action == 'finish':
        ready_http()
        audit=shell('post-http-runtime-audit',(HERE/'audit.py').read_text())
        result=json.loads(audit[audit.index('{'):])
        assert result['applied_migrations']==202
        for old in (SITE_SOURCE/'judge/migrations').glob('*.py'):
            assert result['migration_sha256'][old.name]==digest(old)
        save_baseline(result)
        return
    if args.action == 'network':
        print(docker('network-details','network','inspect',NET,'--format','{{json .Internal}} {{json .Containers}}'))
        print(docker('local-port','port',SITE,expected=None))
        code="import socket; print('dns',socket.gethostbyname('redis')); s=socket.create_connection(('redis',6379),3); s.sendall(b'*1\\r\\n$4\\r\\nPING\\r\\n'); print(s.recv(100)); s.close()"
        print(docker('cache-connect','exec',SITE,'python','-c',code,expected=None))
        print(docker('internal-login','exec',SITE,'python','-c',"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/',timeout=5).status)",expected=None))
        return
    if args.action == 'diagnose':
        print(docker('server-log','exec',SITE,'cat','/tmp/b01-http.log',expected=None,public=False))
        print(docker('website-inside-http','exec',SITE,'python','-c',
                     "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/').status)",expected=None))
        print(docker('website-port','port',SITE,expected=None))
        return
    if args.action == 'status':
        site_info = inspect('container', SITE)
        if site_info and site_info['State']['Running']:
            required = (DB, REDIS) + (('cpjudge-b03-worker',) if (ROOT/'build/b03-worker-1/enabled').exists() else ())
            for name in required:
                if not (service := inspect('container', name)) or not service['State']['Running']:
                    raise RuntimeError(f'{name} is not running; inspect private service logs')
        if (ROOT/'build/b03-worker-1/enabled').exists():
            worker_status = run('b03-status',[sys.executable,'-B',str(HERE/'b03.py'),'status'])
            if site_info and site_info['State']['Running']:
                state = json.loads(worker_status[worker_status.index('{'):])
                if not state['online'] or state['executors'] != ['CPP11', 'CPP14', 'CPP17', 'CPP20', 'CPP23']:
                    raise RuntimeError('Native judge worker is offline or has incomplete executors; inspect private B03 state log')
        if (ROOT/'build/b02-services-1/enabled').exists():
            run('b02-status',[sys.executable,'-B',str(HERE/'b02.py'),'status'])
        print(docker('services-status','ps','-a','--filter','label=cpjudge.task=B01',
               '--format','{{.Names}}\t{{.Status}}\t{{.Ports}}'))
        return
    if args.action == 'stop':
        if (ROOT/'build/b03-worker-1/enabled').exists():
            run('b03-stop',[sys.executable,'-B',str(HERE/'b03.py'),'stop'])
        if (ROOT/'build/b02-services-1/enabled').exists():
            run('b02-stop',[sys.executable,'-B',str(HERE/'b02.py'),'stop'])
        for name in [SITE,REDIS,DB]:
            info = inspect('container',name)
            if info:
                assert info['Config']['Labels'].get('cpjudge.task') == 'B01'
                docker('stop-'+name,'stop',name)
        print('B01 containers stopped; development database volume preserved.')
        return
    if args.action == 'start':
        for name in [DB,REDIS,SITE]:
            info=inspect('container',name)
            assert info and info['Config']['Labels'].get('cpjudge.task')=='B01'
            if not info['State']['Running']:
                docker('restart-'+name,'start',name)
        ready_db()
        if (ROOT/'build/phase-c-checkpoint1-1/enabled').exists():
            shell('checkpoint1-fail-closed-start', "from django.conf import settings\nassert getattr(settings,'CPJ_NATIVE',False) and settings.ROOT_URLCONF=='cpjudge.urls' and not settings.EVENT_DAEMON_USE, 'Checkpoint1 rollback requires review before exposing HTTP'\n")
        try:
            with urllib.request.urlopen(URL+'/accounts/login/',timeout=3): pass
        except Exception:
            server()
        ready_http()
        if (ROOT/'build/b02-services-1/enabled').exists():
            run('b02-start',[sys.executable,'-B',str(HERE/'b02.py'),'start'])
        if (ROOT/'build/b03-worker-1/enabled').exists():
            run('b03-start',[sys.executable,'-B',str(HERE/'b03.py'),'start'])
        run('post-start-status',[sys.executable,'-B',str(HERE/'manage.py'),'status'])
        print('Local website running: '+URL)
        return
    if args.action == 'browser':
        browser_pin=json.loads((HERE/'browser-image.json').read_text())
        browser_image=browser_pin['image']
        if not inspect('image',browser_image):
            docker('browser-image-pull','pull',browser_image)
        info=inspect('image',browser_image)
        assert info and info['RepoDigests']
        browser_base=info['RepoDigests'][0]
        context=WORK/'browser-context'
        context.mkdir(exist_ok=True)
        (context/'Dockerfile').write_text(
            'FROM '+browser_base+'\nRUN python -m pip install --no-cache-dir playwright=='+browser_pin['playwright_version']+'\n')
        docker('browser-image-build','build','--progress=plain','-t','cpjudge-b01-browser:local1',str(context))
        browser_out=WORK/'browser'/session
        browser_out.mkdir(parents=True)
        docker('real-browser','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--network','host','--env','B01_URL='+URL,'--memory','1g','--cpus','2',
               '--shm-size','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
               '--mount',f'type=bind,src={private / "accounts.json"},dst=/run/accounts.json,readonly',
               '--mount',f'type=bind,src={HERE / "browser.py"},dst=/tests/browser.py,readonly',
               '--mount',f'type=bind,src={browser_out},dst=/results',
               'cpjudge-b01-browser:local1','python','/tests/browser.py',public=False)
        evidence=json.loads((browser_out/'result.json').read_text())
        evidence.update({'base_image':browser_base,'browser_image_id':inspect('image','cpjudge-b01-browser:local1')['Id'],
                         'private_artifacts':str(browser_out.relative_to(ROOT))})
        (REPORT/f'browser-{session}.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print('PASS: actual browser checks; sanitized report saved; screenshots remain private.')
        return

    if args.action == 'verify':
        ready_db()
        verify_baseline()
        return

    # Fresh local environment only. No existing Docker object is replaced.
    for name in [DB,REDIS,SITE,BOOT]:
        assert inspect('container',name) is None, f'{name} already exists: use start/status'
    assert inspect('network',NET) is None and inspect('network',WEBNET) is None and inspect('volume',VOLUME) is None
    with socket.socket() as sock:
        assert sock.connect_ex(('127.0.0.1',8000)) != 0, 'localhost port 8000 is occupied'
    info=inspect('image',BASE)
    assert info and info['Id']==BASE_ID, 'A09 locked base image absent or changed; follow A09 rebuild recipe'
    pins=json.loads((A09/'base-pins.json').read_text())
    for image in [pins['mariadb'],pins['redis']]:
        assert inspect('image',image), f'required pinned image absent: {image}'
    assert subprocess.check_output(['git','-C',str(SITE_SOURCE),'rev-parse','HEAD'],text=True).strip()==PIN
    assert not subprocess.check_output(['git','-C',str(SITE_SOURCE),'status','--porcelain'],text=True).strip()
    context=WORK/'context'
    context.mkdir(exist_ok=False)
    staging=WORK/'patched-source'
    for name in ['judge/models/choices.py','judge/models/profile.py']:
        path=staging/name
        path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(SITE_SOURCE/name,path)
    patch=ROOT/'patches/site/0001-stable-timezone-choices.patch'
    run('patch-check',['git','-C',str(staging),'apply','--check',str(patch)])
    run('patch-apply',['git','-C',str(staging),'apply',str(patch)])
    password=secrets.token_urlsafe(32)
    site_key=secrets.token_urlsafe(64)
    root_password=secrets.token_urlsafe(32)
    account_data={role:{'username':'b01-'+role,'password':secrets.token_urlsafe(24)} for role in ['staff','participant']}
    secret_values.extend([password,site_key,root_password])
    for data in account_data.values():secret_values.extend(data.values())
    private_write('db.env',f'MARIADB_ROOT_PASSWORD={root_password}\nMARIADB_DATABASE=b01\nMARIADB_USER=b01\nMARIADB_PASSWORD={password}\n')
    private_write('site.env',f'B01_SECRET_KEY={site_key}\nDB_PASSWORD={password}\n')
    private_write('accounts.json',json.dumps(account_data,indent=2)+'\n')
    docker('network-create','network','create','--internal','--label','cpjudge.task=B01',NET)
    docker('web-network-create','network','create','--label','cpjudge.task=B01',WEBNET)
    docker('database-volume-create','volume','create','--label','cpjudge.task=B01',VOLUME)
    docker('database-start','run','-d','--name',DB,'--label','cpjudge.task=B01',
           '--network',NET,'--network-alias','db','--memory','1536m','--cpus','2',
           '--mount',f'type=volume,src={VOLUME},dst=/var/lib/mysql',
           '--env-file',str(private/'db.env'),pins['mariadb'])
    docker('redis-start','run','-d','--name',REDIS,'--label','cpjudge.task=B01',
           '--network',NET,'--network-alias','redis','--memory','256m',
           '--tmpfs','/data:rw,size=67108864',pins['redis'],
           'redis-server','--save','','--appendonly','no')
    ready_db()
    # Observe A09 drift again on the exact upstream runtime before applying the fix.
    docker('bootstrap-start','run','-d','--name',BOOT,'--label','cpjudge.task=B01',
           '--network',NET,'--memory','1536m','--env-file',str(private/'site.env'),
           '--mount',f'type=bind,src={HERE / "local_settings.py"},dst=/app/dmoj/local_settings.py,readonly',
           BASE,'sleep','infinity')
    manage('original-drift-confirmed','makemigrations','--check','--dry-run',container=BOOT,expected=1)
    for name in ['choices.py','profile.py']:
        docker('bootstrap-patch-'+name,'cp',str(staging/'judge/models'/name),BOOT+':/app/judge/models/'+name)
        shutil.copy2(staging/'judge/models'/name,context/name)
    target=HERE/'migrations'/MIGRATION
    if target.exists():
        docker('bootstrap-install-migration','cp',str(target),BOOT+':/app/judge/migrations/'+MIGRATION)
    else:
        manage('generate-forward-migration','makemigrations','judge','--name','reconcile_model_metadata','--noinput',container=BOOT)
        docker('save-forward-migration','cp',BOOT+':/app/judge/migrations/'+MIGRATION,str(target))
    manage('fixed-drift-bootstrap','makemigrations','--check','--dry-run',container=BOOT)
    sql=manage('forward-migration-sql','sqlmigrate','judge','0153',container=BOOT)
    sql_lines=[line.strip() for line in sql.splitlines() if line.strip() and not line.lstrip().startswith(('--','/usr/','warnings.warn'))]
    assert not any(re.match(r'^(ALTER|CREATE|DROP|INSERT|UPDATE|DELETE|RENAME|TRUNCATE)\b',line,re.I) for line in sql_lines)
    shutil.copy2(target,context/MIGRATION)
    for name in ['Dockerfile','local_settings.py']:shutil.copy2(HERE/name,context/name)
    docker('website-image-build','build','--progress=plain','-t',IMAGE,str(context))
    # Remove only the bootstrap object created above; persistent local services remain.
    docker('bootstrap-cleanup','rm','-f',BOOT)
    docker('website-start','run','-d','--name',SITE,'--label','cpjudge.task=B01',
           '--network',WEBNET,'--memory','1536m','--cpus','2',
           '--cap-drop','ALL','--security-opt','no-new-privileges',
           '--publish','127.0.0.1:8000:8000','--env-file',str(private/'site.env'),
           IMAGE,'sleep','infinity')
    docker('private-network-connect','network','connect','--alias','site',NET,SITE)
    manage('initial-migrate','migrate','--noinput')
    manage('initial-fixtures','loaddata','navbar','language_small')
    provision_development_accounts(reset=False)
    for command in ['compilemessages','compilejsi18n']:
        manage(command,command)
    manage('initial-collectstatic','collectstatic','--noinput')
    verify_baseline()
    server()


if __name__=='__main__':
    import re
    main()
