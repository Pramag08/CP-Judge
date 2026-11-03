"""Private evidence coordinator. Run backup before any Phase C migration."""
import datetime
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'build/phase-c-1'
REPORT = ROOT / 'reports/phase-c-1'
WORK.mkdir(parents=True, exist_ok=True, mode=0o700)
REPORT.mkdir(parents=True, exist_ok=True)
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')

def run(name, args, data=None):
    p = subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log = WORK / (stamp + '-' + name + '.log')
    log.write_bytes(p.stdout + p.stderr)
    log.chmod(0o600)
    path = REPORT / 'commands.json'
    rows = json.loads(path.read_text()) if path.exists() else []
    rows.append({'name': name, 'argv': args, 'exit_status': p.returncode,
                 'private_log': str(log.relative_to(ROOT))})
    path.write_text(json.dumps(rows, indent=2) + '\n')
    print(f'{name}: exit {p.returncode}', flush=True)
    if p.returncode:
        raise RuntimeError(f'{name} failed; inspect private log')
    return p.stdout

if __name__ == '__main__':
    if sys.argv[1] == 'backup':
        # Password expansion happens only inside DB container, never in argv/output.
        data = run('backup', ['docker','exec','cpjudge-b01-db','sh','-c',
            'exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01'])
        path = WORK / (stamp + '-database.sql.gz')
        with path.open('xb') as f:
            os.chmod(path, 0o600)
            f.write(gzip.compress(data))
        recovered = gzip.decompress(path.read_bytes())
        assert recovered == data and b'CREATE TABLE' in recovered and b'-- Dump completed on' in recovered
        (REPORT / 'backup.json').write_text(json.dumps({'status':'PASS', 'readable_gzip_round_trip':True,
            'private_backup':str(path.relative_to(ROOT)), 'restore_test':'NOT RUN'}, indent=2)+'\n')
        print('Private backup saved and successfully read; contents suppressed.')
    elif sys.argv[1] == 'stage-tests':
        run('stage-app', ['docker','cp', str(ROOT/'deploy/phase-c/cpjudge')+'/.', 'cpjudge-b01-site:/app/cpjudge'])
        run('stage-test-settings', ['docker','cp', str(ROOT/'deploy/phase-c/test_settings.py'), 'cpjudge-b01-site:/app/dmoj/cpj_test_settings.py'])
        run('test-database-grant', ['docker','exec','cpjudge-b01-db','sh','-c',
            'exec mariadb --user=root --password="$MARIADB_ROOT_PASSWORD" -e "GRANT ALL ON test_cpj_phase_c.* TO b01;"'])
        run('stage-converter', ['docker','cp',str(ROOT/'compat')+'/.','cpjudge-b01-site:/app/compat'])
        run('stage-converter-pin', ['docker','cp',str(ROOT/'dependencies.json'),'cpjudge-b01-site:/app/dependencies.json'])
        run('stage-pinned-pcc', ['docker','cp','/tmp/cp-judge-pcc/.','cpjudge-b01-site:/tmp/cpj-pcc'])
        sys.path.insert(0,str(ROOT))
        from tools.make_fixtures import build
        build(WORK/'synthetic')
        run('stage-synthetic-package', ['docker','cp',str(WORK/'synthetic/tokens.zip'),'cpjudge-b01-site:/tmp/cpj-tokens.zip'])
        run('generate-additive-migration', ['docker','exec','--user','1000:1000','cpjudge-b01-site','python','manage.py',
            'makemigrations','cpjudge','--settings=dmoj.cpj_test_settings'])
        run('retain-migration', ['docker','cp','cpjudge-b01-site:/app/cpjudge/migrations/.',str(ROOT/'deploy/phase-c/cpjudge/migrations')])
    elif sys.argv[1] == 'test-identity':
        run('stage-tests', ['docker','cp', str(ROOT/'deploy/phase-c/cpjudge')+'/.', 'cpjudge-b01-site:/app/cpjudge'])
        run('identity-tests', ['docker','exec','--user','1000:1000','cpjudge-b01-site','python','manage.py','test',
             'cpjudge.tests','--settings=dmoj.cpj_test_settings','--keepdb','--noinput','-v','2'])
    elif sys.argv[1] == 'browser-identity':
        run('stage-browser-settings', ['docker','cp',str(ROOT/'deploy/phase-c/browser_settings.py'),
            'cpjudge-b01-site:/app/dmoj/cpj_browser_settings.py'])
        code = """import json, os
from django.contrib.auth import get_user_model
from cpjudge.identity import provision
User=get_user_model()
assert not User.objects.filter(username='CPJC1BROWSER').exists(), 'Inspect prior browser fixture rather than reseed'
a=User.objects.create_superuser('c1browseroperator',password=None)
u,p=provision(a,'CPJC1BROWSER',first_name='Browser',email='private@example.invalid')
fd=os.open('/tmp/cpj-c1-fixture.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
os.write(fd,json.dumps({'username':u.username,'password':p}).encode());os.close(fd)
print('Isolated browser fixture prepared privately.')
"""
        run('browser-fixture', ['docker','exec','-i','cpjudge-b01-site','python','manage.py','shell',
             '--settings=dmoj.cpj_browser_settings'], code.encode())
        browser_work=WORK/('browser-'+stamp)
        browser_work.mkdir(mode=0o700)
        run('browser-private-credential', ['docker','cp','cpjudge-b01-site:/tmp/cpj-c1-fixture.json',str(browser_work/'account.json')])
        os.chmod(browser_work/'account.json',0o600)
        run('isolated-browser-server', ['docker','exec','-d','cpjudge-b01-site','sh','-c',
            'exec python manage.py runserver 0.0.0.0:8001 --noreload --settings=dmoj.cpj_browser_settings > /tmp/cpj-c1-browser.log 2>&1'])
        run('chromium-identity', ['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}',
             '--network','container:cpjudge-b01-site','--shm-size','256m','--cap-drop','ALL',
             '--security-opt','no-new-privileges','--mount',f'type=bind,src={browser_work},dst=/results',
             '--mount',f'type=bind,src={ROOT/"deploy/phase-c/browser_identity.py"},dst=/tests/browser.py,readonly',
             'cpjudge-b01-browser:local1','python','/tests/browser.py'])
        (REPORT/'identity-browser.json').write_bytes((browser_work/'browser.json').read_bytes())
    elif sys.argv[1] == 'resume-browser':
        browser_work=max(WORK.glob('browser-*'))
        run('chromium-identity', ['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}',
             '--network','container:cpjudge-b01-site','--shm-size','256m','--cap-drop','ALL',
             '--security-opt','no-new-privileges','--mount',f'type=bind,src={browser_work},dst=/results',
             '--mount',f'type=bind,src={ROOT/"deploy/phase-c/browser_identity.py"},dst=/tests/browser.py,readonly',
             'cpjudge-b01-browser:local1','python','/tests/browser.py'])
        (REPORT/'identity-browser.json').write_bytes((browser_work/'browser.json').read_bytes())
    elif sys.argv[1] == 'recover-browser':
        browser_work=max(WORK.glob('browser-*'))
        credential='/tmp/cpj-recovery-'+stamp+'.json'
        run('offline-organizer-recovery', ['docker','exec','cpjudge-b01-site','python','manage.py',
            'college_account','reset','CPJC1BROWSER','--actor','c1browseroperator','--credential-file',credential,
            '--settings=dmoj.cpj_browser_settings'])
        run('recovery-private-credential', ['docker','cp','cpjudge-b01-site:'+credential,str(browser_work/'recovery-account.json')])
        os.chmod(browser_work/'recovery-account.json',0o600)
        run('chromium-recovery', ['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}',
             '--network','container:cpjudge-b01-site','--shm-size','256m','--cap-drop','ALL',
             '--security-opt','no-new-privileges','--mount',f'type=bind,src={browser_work},dst=/results',
             '--mount',f'type=bind,src={ROOT/"deploy/phase-c/browser_identity.py"},dst=/tests/browser.py,readonly',
             'cpjudge-b01-browser:local1','python','/tests/browser.py','recovery'])
        (REPORT/'recovery-browser.json').write_bytes((browser_work/'recovery-browser.json').read_bytes())
    elif sys.argv[1] == 'stop-browser':
        code="""import os,signal
from pathlib import Path
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:args=(p/'cmdline').read_bytes().split(bytes([0]))
 except OSError:continue
 if b'manage.py' in args and b'runserver' in args and b'--settings=dmoj.cpj_browser_settings' in args:
  os.kill(int(p.name),signal.SIGTERM)
print('Isolated Phase C browser server stopped; live Phase B server untouched.')
"""
        run('stop-isolated-server',['docker','exec','-i','cpjudge-b01-site','python'],code.encode())
    elif sys.argv[1] == 'preserve':
        before=gzip.decompress((ROOT/json.loads((REPORT/'backup.json').read_text())['private_backup']).read_bytes())
        after=run('preservation-private-dump', ['docker','exec','cpjudge-b01-db','sh','-c',
            'exec mariadb-dump --user=root --password="$MARIADB_ROOT_PASSWORD" --single-transaction --routines --events --databases b01'])
        import re
        def rows(data):
            return {m[1].decode():m[0] for m in re.finditer(rb'^INSERT INTO `([^`]+)`.*$',data,re.M)}
        old,new=rows(before),rows(after)
        protected=('auth_user','judge_profile','judge_contest','judge_contestparticipation','judge_contestproblem',
            'judge_contestsubmission','judge_submission','judge_submissionsource','judge_submissiontestcase','django_migrations')
        for table in protected:
            assert table in old and old[table]==new[table], 'Baseline table changed: '+table
        run('live-settings-and-counts', ['docker','exec','-i','cpjudge-b01-site','python','manage.py','shell'], b"from django.conf import settings\nfrom judge.models import Submission,SubmissionTestCase,Judge\nassert not any(a.startswith('cpjudge') for a in settings.INSTALLED_APPS)\nassert Submission.objects.count()==12 and SubmissionTestCase.objects.count()==1030\nassert Judge.objects.get(name='cpjudge-local-worker').online\nprint('Live Phase B app list unchanged; 12 submissions, 1030 cases, worker online.')\n")
        (REPORT/'preservation.json').write_text(json.dumps({'status':'PASS','baseline_insert_rows_identical':list(protected),
            'live_phase_c_enabled':False,'existing_submissions':12,'existing_cases':1030,'worker_online':True,
            'isolated_test_database':'test_cpj_phase_c'},indent=2)+'\n')
    else:
        raise SystemExit('Usage: coordinator.py backup|stage-tests|test-identity|browser-identity')
