"""Bounded B04/B05 operator installation; never submit or publish problems."""
import argparse
import datetime
import fcntl
import grp
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import http.client
import urllib.parse
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
SITE = 'cpjudge-b01-site'
WORKER = 'cpjudge-b03-worker'
SOURCE = ROOT / 'build/a09-site-1/site'
PACKAGE = ROOT / 'local-packages/gaming-grid.zip'
CONVERSION = ROOT / 'build/a02-converter-1/pipeline/converted-3'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'snapshot', 'install', 'verify', 'privacy', 'preserve', 'cleanup-sessions', 'diagnose-preservation', 'restore-diagnostic-access'])
    parser.add_argument('--revision', type=int, default=1)
    args = parser.parse_args()
    assert 1 <= args.revision < 10**18
    if grp.getgrnam('docker').gr_gid not in [os.getgid(), *os.getgroups()]:
        os.execvp('sg', ['sg', 'docker', '-c', shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), *sys.argv[1:]])])
    phase = 'b04-installation-1' if args.action == 'plan' else 'b05-problem-1'
    work, out = ROOT / 'build' / phase, Path(os.environ.get('CPJ_PROBLEM_REPORT', ROOT / 'reports' / phase))
    work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    lock = (work / 'operator.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    private = work / 'private'; private.mkdir(exist_ok=True, mode=0o700); private.chmod(0o700)
    secrets = [json.loads((ROOT / 'build/b03-worker-1/private/worker.json').read_text())['key']]
    for row in json.loads((ROOT / 'build/b01-site-1/private/accounts.json').read_text()).values():
        secrets.extend(row.values())
    for p in (ROOT / 'build/b01-site-1/private').glob('*.env'):
        secrets.extend(line.split('=', 1)[1] for line in p.read_text().splitlines() if '=' in line)

    def run(name, argv, stdin=None, public=True):
        print(name + ': running', flush=True)
        p = subprocess.run(argv, input=stdin, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        raw = work / 'logs' / stamp / (name + '.log'); raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(p.stdout); raw.chmod(0o600)
        safe = p.stdout
        for value in sorted(secrets, key=len, reverse=True):
            if len(value) >= 6:
                safe = safe.replace(value, '[REDACTED]')
        dest = out / 'logs' / stamp / raw.name
        if public:
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(safe)
        ledger = out / 'commands.json'
        rows = json.loads(ledger.read_text()) if ledger.exists() else []
        rows.append({'action': args.action, 'name': name, 'argv': argv, 'exit_status': p.returncode,
                     'timestamp_utc': stamp, 'log': str((dest if public else raw).relative_to(ROOT))})
        ledger.write_text(json.dumps(rows, indent=2) + '\n')
        print(name + ': exit ' + str(p.returncode), flush=True)
        assert p.returncode == 0, name + ' failed; see recorded log'
        return p.stdout

    def docker(name, *argv, **kw):
        return run(name, ['docker', *argv], **kw)

    def shell(name, code, public=True):
        output = docker(name, 'exec', '-i', SITE, 'python', 'manage.py', 'shell', stdin=code, public=public)
        return json.loads(output[output.index('OPERATOR_RESULT=') + len('OPERATOR_RESULT='):])

    if args.action == 'plan':
        from tools.verify_install import verify
        import yaml
        from defusedxml import ElementTree as ET
        observed = verify(PACKAGE, CONVERSION)
        assert observed['tests_verified'] == 103 and observed['statement_assets_verified'] == 15
        historical = json.loads((ROOT / 'reports/a02-converter-1/evidence.json').read_text())['preservation']['gaming-grid']
        assert observed == historical, 'Existing package/conversion differs from A02 evidence'
        code = 'pv' + str(args.revision).zfill(18)
        with zipfile.ZipFile(PACKAGE) as src:
            xml = ET.fromstring(src.read('problem.xml'))
            tests = xml.find('judging/testset')
            limits = {'source_time_ms': int(tests.findtext('time-limit')), 'source_memory_bytes': int(tests.findtext('memory-limit'))}
        conf = yaml.safe_load((CONVERSION / 'gaming-grid/init.yml').read_text())
        assert conf['checker'] == {'name': 'bridged', 'args': {'files': ['checker.cpp', 'testlib.h'], 'lang': 'CPP23', 'type': 'testlib'}}
        assert conf['short_circuit'] is False and len(conf['test_cases']) == 103
        assert all(c == {'in': f'{i}.in', 'out': f'{i}.out', 'points': 1} for i, c in enumerate(conf['test_cases'], 1))
        paths = ['judge/models/problem.py', 'judge/models/submission.py', 'judge/judgeapi.py',
                 'judge/bridge/judge_handler.py', 'judge/views/problem_data.py', 'dmoj/urls.py']
        expected = {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() for name in paths}
        runtime = shell('selected-site-models', 'EXPECTED=' + repr(expected) + '\n' + (HERE / 'problem_inspect.py').read_text())
        worker = docker('native-worker-source', 'exec', '-i', WORKER, '/env/bin/python3', '-', stdin=(HERE / 'problem_worker_inspect.py').read_text())
        worker = json.loads(worker)
        mapping = {'status': 'PASS', 'task': 'B04 only', 'source_pin': runtime['site_pin'],
                   'worker_pin': worker['pin'], 'source_checks': expected, 'worker_source_checks': worker['source_sha256'],
                   'display_identity': 'gaming-grid', 'revision': args.revision, 'native_code': code,
                   'package_sha256': observed['source_sha256'], **limits,
                   'site_values': {'time_limit': 2.0, 'memory_limit': 262144, 'short_circuit': False,
                                   'points': 103.0, 'partial': True, 'is_public': False, 'is_manually_managed': True,
                                   'allowed_languages': ['CPP23'], 'description': ''},
                   'expected_worker_request': {'problem-id': code, 'language': 'CPP23', 'time-limit': 2.0,
                                               'memory-limit': 262144, 'short-circuit': False},
                   'checker': conf['checker'], 'ordered_cases': 103, 'raw_case_points': 103,
                   'sample_count': 1, 'sample_indices': [1], 'statement_asset_count': 15,
                   'language_limits': 'none; reject conflicting overrides',
                   'immutable_identity': 'opaque 18-digit operator revision plus full canonical manifest/package digests',
                   'publication': 'private pending B06 and judging/readiness gates', 'judging': 'NOT TESTED',
                   'native_groups_available': runtime['groups'], 'runtime_CPP23_online': runtime['CPP23_online'],
                   'category': {'name': 'localpolygon', 'full_name': 'Private Polygon imports'},
                   'inspected_worker_limits': worker['limit_semantics']}
        assert limits == {'source_time_ms': 2000, 'source_memory_bytes': 268435456}
        assert runtime['CPP23_online'] and conf['time_limit'] == 2.0 and conf['memory_limit'] == 262144
        (out / 'mapping.json').write_text(json.dumps(mapping, indent=2) + '\n')
        print('PASS: B04 mapping and source/package inspection; no database/problem mutation.')
        return
    mapping = json.loads((ROOT / 'reports/b04-installation-1/mapping.json').read_text())
    review = json.loads((ROOT / 'reports/b04-installation-1/review.json').read_text())
    assert review['status'] == 'PASS'
    for name, sha in review['inspected_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, 'Reviewed B04 input changed: ' + name
    assert args.revision == mapping['revision'], 'Define/review a new B04 revision mapping first'
    if args.action == 'cleanup-sessions':
        keys = []
        for path in (work / 'logs').glob('*/temporary-privacy-session.log'):
            text = path.read_text()
            if 'OPERATOR_RESULT=' in text:
                keys.append(json.loads(text.split('OPERATOR_RESULT=', 1)[1])['key'])
        secrets.extend(keys)
        cleanup = shell('delete-all-owned-diagnostic-sessions', 'KEYS=' + repr(keys) + '\n' + (HERE / 'problem_session_cleanup.py').read_text())
        (out / ('session-cleanup-' + stamp + '.json')).write_text(json.dumps(cleanup, indent=2) + '\n')
        return
    if args.action in ('snapshot', 'preserve', 'diagnose-preservation', 'restore-diagnostic-access'):
        result = shell('database-' + args.action, 'MODE=' + repr(args.action) + '\n' + (HERE / 'problem_preserve.py').read_text())
        (out / (args.action + '-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        if args.action == 'snapshot':
            paths = [ROOT / 'build/b03-worker-1/private/config.yml', ROOT / 'build/b03-worker-1/private/worker.json',
                     HERE / 'b03.py', HERE / 'b03_guard.py', HERE / 'b02_config.py']
            (private / 'preserved-source.json').write_text(json.dumps({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, indent=2))
        else:
            for name, sha in json.loads((private / 'preserved-source.json').read_text()).items():
                assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
        print('PASS: ' + args.action + '; private row/config state retained.')
        return

    from tools.site_problem import file_manifest, canonical_digest, install_directory
    from tools.verify_install import verify
    source = CONVERSION / 'gaming-grid'
    request = dict(mapping)
    request['title'] = json.loads((CONVERSION / 'gaming-grid.metadata.json').read_text())['title']
    files = file_manifest(source)
    manifest = {'schema': 1, 'native_code': mapping['native_code'], 'revision': mapping['revision'],
                'package_sha256': mapping['package_sha256'], 'converter_pin': '41ce3afcedf6c02793b308ba2e6ddb2ea5f82134',
                'site_values': mapping['site_values'], 'title': request['title'], 'category': mapping['category'], 'files': files}
    digest = canonical_digest(manifest)
    request['judge_manifest_digest'] = digest
    registry_path = private / 'registry.json'
    parent = ROOT / 'build/b03-worker-1/problems'
    destination = parent / mapping['native_code']

    def models(mode):
        return shell('native-models-' + mode, 'MODE=' + repr(mode) + '\nREQUEST=' + repr(request) + '\n' + (HERE / 'problem_models.py').read_text())

    def registry():
        data = json.loads(registry_path.read_text())
        assert data['manifest_digest'] == digest and data['manifest'] == manifest, 'Revision already bound to different bytes/metadata'
        return data

    if args.action == 'install':
        verified = verify(PACKAGE, CONVERSION)
        assert verified['source_sha256'] == mapping['package_sha256'] and verified['tests_verified'] == 103
        preflight = models('preflight')
        if not registry_path.exists():
            assert not destination.exists() and not preflight['exists'], 'Refusing adoption of an unregistered existing code/path'
            fd = os.open(registry_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.write(fd, json.dumps({'manifest_digest': digest, 'manifest': manifest}, indent=2).encode()); os.close(fd)
        registry()
        assert parent.is_dir() and not parent.is_symlink()
        parent.chmod(0o700)  # Worker UID equals operator UID; other host users cannot traverse private data.
        files_created = install_directory(source, parent, mapping['native_code'], files)
        installed = models('install')
        docker('native-problem-refresh', 'kill', '--signal', 'SIGUSR2', WORKER)
        for _ in range(20):
            state = models('verify')
            if state['native_worker_recognizes_problem']:
                break
            time.sleep(.5)
        else:
            raise RuntimeError('Actual worker did not advertise installed code')
        result = {'status': 'PASS', 'task': 'B05 installation only', 'native_code': mapping['native_code'],
                  'revision': mapping['revision'], 'manifest_digest': digest, 'package_sha256': verified['source_sha256'],
                  'directory_created': files_created, 'problem_created': installed['created'], 'problem_pk': installed['problem_pk'],
                  'all_source_checks': verified, 'native_worker_recognizes_problem': True, 'judging': 'NOT TESTED'}
        (out / ('installation-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        print('PASS: private installation and actual native worker advertisement; no submission.')
        return

    registry()
    assert parent.stat().st_mode & 0o777 == 0o700, 'Private worker data parent must restrict host traversal'
    assert file_manifest(destination) == files, 'Installed bytes differ from immutable manifest'
    if args.action == 'verify':
        verified = verify(PACKAGE, CONVERSION)
        state = models('verify')
        assert state['native_worker_recognizes_problem']
        case_hashes = json.loads((CONVERSION / 'conversion-report.json').read_text())['test_hashes']
        code = 'REQUEST=' + repr(request) + '\nFILES=' + repr(files) + '\nCASE_HASHES=' + repr(case_hashes) + '\n' + (HERE / 'problem_worker_verify.py').read_text()
        worker = json.loads(docker('actual-worker-installed-bytes', 'exec', '-i', WORKER, '/bin/bash', '-c',
                                  '. ~judge/.profile; export HOME=/tmp; exec /env/bin/python3 -', stdin=code))
        result = {'status': 'PASS', 'native_code': mapping['native_code'], 'manifest_digest': digest,
                  'source_verification': verified, 'site_and_advertisement': state, 'actual_worker': worker,
                  'expected_worker_request': mapping['expected_worker_request'], 'judging': 'NOT TESTED'}
        (out / ('verification-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        print('PASS: exact source/site/worker bytes, limits and CPP23 mapping.')
        return
    if args.action == 'privacy':
        session = shell('temporary-privacy-session', (HERE / 'problem_privacy_session.py').read_text(), public=False)
        secrets.append(session['key'])
        try:
            categories = {'native_data': [], 'web_static_media': [], 'private_package_paths': []}
            categories['native_data'] = ['/problem/' + mapping['native_code'] + '/data/' + row['path'] for row in files]
            categories['native_data'] += ['/problem/' + mapping['native_code'] + '/data/' + str(i) + '.' + suffix for i in range(1, 104) for suffix in ('in', 'out')]
            categories['native_data'] += ['/problem/' + mapping['native_code'] + '/test_data', '/problem/' + mapping['native_code'] + '/test_data/init']
            for prefix in ('/static/', '/media/', '/problems/', '/static/problems/', '/media/problems/'):
                categories['web_static_media'] += [prefix + mapping['native_code'] + '/' + row['path'] for row in files]
            with zipfile.ZipFile(PACKAGE) as archive:
                names = [name for name in archive.namelist() if name.startswith(('solutions/', 'checkers/')) and name.endswith(('.cpp', '.h'))]
                from defusedxml import ElementTree as ET
                xml = ET.fromstring(archive.read('problem.xml'))
                names += [element.get('path') for element in xml.findall('assets/checker/source') + xml.findall('assets/solutions/solution/source') if element.get('path')]
                checker_path = Path(xml.find('assets/checker/source').get('path'))
                names += [str(checker_path.parent / name) for name in mapping['checker']['args']['files'] if name != 'checker.cpp']
                names = sorted(set(names))
            for prefix in ('/static/', '/media/', '/problem/' + mapping['native_code'] + '/data/'):
                categories['private_package_paths'] += [prefix + name for name in names]
            categories['private_package_paths'] += ['/local-packages/gaming-grid.zip', '/static/local-packages/gaming-grid.zip', '/media/local-packages/gaming-grid.zip',
                '/build/b03-worker-1/problems/' + mapping['native_code'] + '/data.zip', '/problem/' + mapping['native_code'] + '/data/../data.zip']
            counts = {}
            for role, headers in [('anonymous', {}), ('ordinary_participant', {'Cookie': session['cookie_name'] + '=' + session['key']})]:
                conn = http.client.HTTPConnection('127.0.0.1', 8000, timeout=10)
                conn.request('GET', '/edit/profile/', headers=headers)
                response = conn.getresponse(); response.read()
                assert response.status == (302 if role == 'anonymous' else 200), 'Authentication control failed'
                counts[role] = {}
                for category, urls in categories.items():
                    statuses = {}
                    for url in urls:
                        conn.request('GET', urllib.parse.quote(url, safe='/._-'), headers=headers)
                        response = conn.getresponse(); response.read()
                        assert response.status in (302, 403, 404), (category, response.status)
                        if response.status == 302:
                            assert response.getheader('Location', '').startswith('/accounts/login/')
                        statuses[str(response.status)] = statuses.get(str(response.status), 0) + 1
                    counts[role][category] = statuses
                conn.close()
            result = {'status': 'PASS', 'actual_http_roles_verified': True, 'responses': counts,
                      'source_reference_checker_hidden_routes_denied': True,
                      'public_static_media_downloads_denied': True, 'statement_rendering': 'NOT TESTED',
                      'judging': 'NOT TESTED'}
            (out / ('privacy-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
            print('PASS: real anonymous/participant HTTP requests denied private data/static/source downloads.')
        finally:
            shell('remove-only-temporary-privacy-session', "import importlib,json\nfrom pathlib import Path\nfrom django.conf import settings\np=Path('/tmp/b05-privacy-session.json');s=json.loads(p.read_text());store=importlib.import_module(settings.SESSION_ENGINE).SessionStore(session_key=s['key']);store.delete();assert store.load()=={};p.unlink()\nprint('OPERATOR_RESULT='+json.dumps({'temporary_session_database_and_cache_deleted':True}))")
        return


if __name__ == '__main__':
    main()
