"""B03 native worker lifecycle and focused evidence; credentials stay in build/."""
import argparse
import datetime
import grp
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import secrets as secret_gen
import time
import fcntl
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WORK = ROOT / 'build/b03-worker-1'
OUT = Path(os.environ.get('CPJ_SITE_REPORT_DIR', ROOT / 'reports/b03-worker-1'))
SITE = 'cpjudge-b01-site'
WORKER = 'cpjudge-b03-worker'
IMAGE = 'sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8'
EXECUTORS = ['CPP11', 'CPP14', 'CPP17', 'CPP20', 'CPP23']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect', 'setup', 'start', 'stop', 'status', 'verify', 'snapshot', 'preserve', 'capabilities', 'logs', 'acceptance'])
    args = parser.parse_args()
    if grp.getgrnam('docker').gr_gid not in [os.getgid(), *os.getgroups()]:
        os.execvp('sg', ['sg', 'docker', '-c', shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), args.action])])
    WORK.mkdir(parents=True, exist_ok=True)
    lock = (WORK / 'lifecycle.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX)
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('CPJ_SITE_REPORT_DIR', str(OUT))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    logs = OUT / 'logs' / stamp
    logs.mkdir(parents=True)
    private = WORK / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    private.chmod(0o700)
    secrets = []
    credential = private / 'worker.json'
    if credential.exists():
        secrets.append(json.loads(credential.read_text())['key'])
    for path in (ROOT / 'build/b01-site-1/private').glob('*.env'):
        secrets.extend(line.split('=', 1)[1] for line in path.read_text().splitlines() if '=' in line)
    accounts = ROOT / 'build/b01-site-1/private/accounts.json'
    if accounts.exists():
        for row in json.loads(accounts.read_text()).values():
            secrets.extend(row.values())

    def run(name, argv, stdin=None, public=True):
        print(name + ': running', flush=True)
        p = subprocess.run(argv, input=stdin, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        raw = WORK / 'logs' / stamp / (name + '.log')
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(p.stdout)
        raw.chmod(0o600)
        safe = p.stdout
        for value in sorted(secrets, key=len, reverse=True):
            if len(value) >= 6:
                safe = safe.replace(value, '[REDACTED]')
        target = logs / raw.name
        if public:
            target.write_text(safe)
        ledger = OUT / 'commands.json'
        rows = json.loads(ledger.read_text()) if ledger.exists() else []
        rows.append({'action': args.action, 'name': name, 'argv': argv, 'exit_status': p.returncode,
                     'timestamp_utc': stamp, 'log': str((target if public else raw).relative_to(ROOT))})
        ledger.write_text(json.dumps(rows, indent=2) + '\n')
        print(name + ': exit ' + str(p.returncode), flush=True)
        if p.returncode:
            raise RuntimeError(name + ' failed; see recorded log')
        return p.stdout

    def docker(name, *argv, **kw):
        return run(name, ['docker', *argv], **kw)

    def shell(name, code):
        return docker(name, 'exec', '-i', SITE, 'python', 'manage.py', 'shell', stdin=code)

    def inspect(name):
        p = subprocess.run(['docker', 'inspect', name], text=True, capture_output=True)
        return json.loads(p.stdout)[0] if p.returncode == 0 else None

    if args.action == 'inspect':
        shell('existing-cpp-language-mapping', "import json\nfrom judge.models import Language,Judge,RuntimeVersion\nprint(json.dumps({'languages':list(Language.objects.filter(key__in=['CPP11','CPP14','CPP17','CPP20','CPP23']).values()),'judges':Judge.objects.count(),'runtime_versions':RuntimeVersion.objects.count()},indent=2))")
        print(docker('image-identity', 'image', 'inspect', IMAGE, '--format', '{{.Id}} {{json .Config.Labels}}'))
        code = "from pathlib import Path\nfor n in ['main.py','judgeenv.py','judge.py','executors/CPP23.py','executors/CPP20.py','executors/gcc_executor.py','executors/base_executor.py','executors/compiled_executor.py','executors/mixins.py','cptbox/handlers.py','cptbox/isolate.py']:\n p=Path('/judge/dmoj')/n\n print('SOURCE',n);print(p.read_text() if p.exists() else 'ABSENT')\nprint('DOCKER FLAG REFERENCES')\nfor p in Path('/judge/dmoj').rglob('*.py'):\n for i,l in enumerate(p.read_text().splitlines(),1):\n  if 'DMOJ_IN_DOCKER' in l:print(str(p),i,l)\n"
        docker('pinned-worker-source', 'run', '--rm', '--network', 'none', '--entrypoint', '/env/bin/python3', IMAGE, '-c', code)
        return

    if args.action in ('snapshot', 'preserve'):
        code = (HERE / 'b03_preserve.py').read_text()
        expected = json.loads((ROOT / 'reports/b01-followup-1/runtime-final.json').read_text())
        output = shell('database-' + args.action, 'MODE=' + repr(args.action) + '\nEXPECTED=' + repr(expected) + '\n' + code)
        data = json.loads(output[output.index('{'):])
        (OUT / ('preservation-' + stamp + '.json')).write_text(json.dumps(data, indent=2) + '\n')
        return

    if args.action == 'setup':
        assert inspect(IMAGE)['Id'] == IMAGE
        assert inspect(WORKER) is None, 'Existing worker: use start/status'
        ident = json.loads(credential.read_text()) if credential.exists() else {'id': 'cpjudge-local-worker', 'key': secret_gen.token_urlsafe(48)}
        secrets.append(ident['key'])
        if not credential.exists():
            fd = os.open(credential, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.write(fd, json.dumps(ident).encode()); os.close(fd)
        runtime = docker('pinned-runtime-config', 'run', '--rm', '--network', 'none', '--entrypoint', 'cat', IMAGE, '/judge-runtime-paths.yml')
        config = private / 'config.yml'
        # JSON quoted scalars are valid YAML; exact autoconfig paths remain unchanged.
        config.write_text(runtime + '\nid: ' + json.dumps(ident['id']) + '\nkey: ' + json.dumps(ident['key']) + '\nproblem_storage_globs: ["/problems/*"]\n')
        config.chmod(0o600)
        uid = int(docker('worker-uid', 'run', '--rm', '--network', 'none', '--entrypoint', 'id', IMAGE, '-u').strip())
        assert uid == os.getuid(), 'Private config must be readable only by actual judge UID'
        docker('private-registration-copy', 'exec', '-i', SITE, 'python', '-c',
               "import os,sys;from pathlib import Path;p=Path('/tmp/b03-registration.json');data=sys.stdin.buffer.read();assert not p.exists() or p.read_bytes()==data;fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600);os.write(fd,data);os.close(fd)", stdin=json.dumps(ident))
        shell('native-registration', (HERE / 'b03_register.py').read_text())
        problems = WORK / 'problems'; problems.mkdir(exist_ok=True)
        docker('worker-create', 'create', '--name', WORKER, '--label', 'cpjudge.task=B03',
               '--network', 'container:' + SITE, '--read-only', '--cap-drop', 'ALL', '--cap-add', 'SYS_PTRACE',
               '--security-opt', 'no-new-privileges', '--pids-limit', '128', '--memory', '2g', '--cpus', '2',
               '--tmpfs', '/tmp:rw,exec,nosuid,size=1g,mode=1777', '--env', 'DMOJ_IN_DOCKER=',
               '--mount', f'type=bind,src={config},dst=/config.yml,readonly',
               '--mount', f'type=bind,src={problems},dst=/problems,readonly',
               '--entrypoint', '/bin/bash', IMAGE, '-c',
               '. ~judge/.profile; export HOME=/tmp; exec /env/bin/dmoj -c /config.yml --no-ansi --only-executors ' + ','.join(EXECUTORS) + ' 127.0.0.1')
        (WORK / 'enabled').write_text('B03 native worker lifecycle enabled\n')
        return

    if args.action == 'logs':
        docker('worker-log', 'logs', WORKER)
        docker('bridge-log', 'exec', SITE, 'cat', '/tmp/b02-bridge.log')
        return

    if args.action == 'acceptance':
        def call(action):
            return run('acceptance-' + action, [sys.executable, '-B', str(HERE / 'b03.py'), action])
        # Child lifecycle calls take the same lock; release it while coordinating.
        fcntl.flock(lock, fcntl.LOCK_UN)
        before = inspect(WORKER)
        call('verify')
        run('idempotent-full-start', [sys.executable, '-B', str(HERE / 'manage.py'), 'start'])
        after = inspect(WORKER)
        assert before['Id'] == after['Id'] and before['State']['Pid'] == after['State']['Pid']
        call('stop'); call('status')
        call('start'); call('verify')
        run('full-lifecycle-stop', [sys.executable, '-B', str(HERE / 'manage.py'), 'stop'])
        assert all(not inspect(n)['State']['Running'] for n in [WORKER, SITE, 'cpjudge-b01-db', 'cpjudge-b01-redis', 'cpjudge-b02-events'])
        run('full-lifecycle-start', [sys.executable, '-B', str(HERE / 'manage.py'), 'start'])
        call('verify'); call('preserve')
        (OUT / 'acceptance.json').write_text(json.dumps({'status': 'PASS', 'worker_disconnect_reconnect': True,
            'native_offline_online_and_website_status': True, 'full_stop_start': True,
            'idempotent_start_same_container_pid': True, 'all_services_stopped_between_restart': True,
            'website_judging': 'NOT TESTED'}, indent=2) + '\n')
        return

    if args.action == 'capabilities':
        output = docker('native-executor-capabilities', 'exec', '-i', WORKER, '/bin/bash', '-c',
                        '. ~judge/.profile; export HOME=/tmp; exec /env/bin/python3 -',
                        stdin=(HERE / 'b03_capabilities.py').read_text())
        data = json.loads(output[output.index('B03_RESULT=') + len('B03_RESULT='):])
        (OUT / ('capabilities-' + stamp + '.json')).write_text(json.dumps(data, indent=2) + '\n')
        return

    info = inspect(WORKER)
    if info:
        assert info['Config']['Labels'].get('cpjudge.task') == 'B03'
        assert info['Image'] == IMAGE
    if args.action == 'stop':
        site_running = inspect(SITE)['State']['Running']
        if site_running:
            shell('worker-stop-idle-guard', "from judge.models import Submission\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nprint('No in-progress submissions; safe worker stop.')")
        if info and info['State']['Running']:
            # Native main catches KeyboardInterrupt for cleanup; container PID 1
            # otherwise ignores the image's default SIGTERM until Docker kills it.
            docker('worker-stop', 'stop', '--signal', 'SIGINT', '--time', '20', WORKER)
            stopped = inspect(WORKER)
            assert stopped['State']['ExitCode'] == 0 and not stopped['State']['OOMKilled']
        if site_running:
            for _ in range(20):
                output = shell('wait-native-offline', (HERE / 'b03_state.py').read_text())
                state = json.loads(output[output.index('{'):])
                if not state['online'] and not state['runtime_versions']:
                    break
                time.sleep(1)
            else:
                raise RuntimeError('Native offline transition not observed')
        return
    if args.action == 'start':
        assert info, 'Run B03 setup first'
        if not info['State']['Running']:
            docker('worker-start', 'start', WORKER)
        for _ in range(45):
            output = shell('wait-native-online', (HERE / 'b03_state.py').read_text())
            state = json.loads(output[output.index('{'):])
            if state['online']:
                assert state['executors'] == EXECUTORS
                if (ROOT / 'build/phase-c-c11-1/enabled').exists():
                    run('ensure-private-readiness-verifier', [sys.executable, '-B', str(HERE / 'worker_readiness.py'), 'start'])
                return
            time.sleep(1)
        raise RuntimeError('Worker did not authenticate within 45 seconds')
    if args.action in ('status', 'verify'):
        print(docker('worker-container-status', 'inspect', WORKER, '--format', '{{.State.Status}} {{.Image}}'))
        if inspect(SITE)['State']['Running']:
            output = shell('native-worker-state', (HERE / 'b03_state.py').read_text())
            data = json.loads(output[output.index('{'):])
            data['worker_container_exit_code'] = info['State']['ExitCode']
            data['worker_oom_killed'] = info['State']['OOMKilled']
            if args.action == 'verify':
                assert data['online'] and data['executors'] == EXECUTORS, data
                capability = json.loads(sorted(OUT.glob('capabilities-*.json'))[-1].read_text())
                wanted = [{'language__key': key, 'name': name, 'version': '.'.join(map(str, version))}
                          for key in EXECUTORS for name, version in capability['executors'][key]['compiler_versions']]
                assert data['runtime_versions'] == wanted
            # The scoped native policy denies the old public status page. Judge
            # registration above is the authoritative worker state; the HTTP
            # checks here only confirm that the site and policy are responding.
            with urllib.request.urlopen('http://127.0.0.1:8000/accounts/login/', timeout=5) as response:
                assert response.status == 200, 'Website login page is not ready'
            try:
                with urllib.request.urlopen('http://127.0.0.1:8000/status/', timeout=5):
                    pass
            except urllib.error.HTTPError as error:
                assert error.code == 401, 'Unexpected anonymous status-page response'
            else:
                raise RuntimeError('Anonymous status page unexpectedly accessible')
            data['website_login_http'] = 200
            data['anonymous_status_http'] = 401
            (OUT / ('sandbox-' + stamp + '.json')).write_text(json.dumps({
                'image': info['Image'], 'user': info['Config']['User'],
                'network_mode': info['HostConfig']['NetworkMode'],
                'read_only_root': info['HostConfig']['ReadonlyRootfs'],
                'cap_drop': info['HostConfig']['CapDrop'], 'cap_add': info['HostConfig']['CapAdd'],
                'security_opt': info['HostConfig']['SecurityOpt'], 'pids_limit': info['HostConfig']['PidsLimit'],
                'memory': info['HostConfig']['Memory'], 'nano_cpus': info['HostConfig']['NanoCpus'],
                'tmpfs': info['HostConfig']['Tmpfs'],
                'mounts': [{'destination': m['Destination'], 'read_only': not m['RW']} for m in info['Mounts']],
                'ports': info['HostConfig']['PortBindings'],
                'worker_api_disabled': 'DMOJ_IN_DOCKER=' in info['Config']['Env']
            }, indent=2) + '\n')
            (OUT / ('state-' + stamp + '.json')).write_text(json.dumps(data, indent=2) + '\n')
            print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
