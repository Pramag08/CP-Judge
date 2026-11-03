"""B06/B07 coordinator. Raw statements, source, cookies and judge logs stay ignored."""
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
import zipfile
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CODE = 'pv000000000000000001'
SITE = 'cpjudge-b01-site'
WORKER = 'cpjudge-b03-worker'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'prepare', 'install', 'browser', 'preserve', 'inspect', 'inspect-submit', 'snapshot-submit', 'preserve-submit', 'instrument', 'submit', 'results'])
    args = parser.parse_args()
    if grp.getgrnam('docker').gr_gid not in [os.getgid(), *os.getgroups()]:
        os.execvp('sg', ['sg', 'docker', '-c', shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), args.action])])
    phase = 'b07-submission-1' if args.action in ('instrument', 'submit', 'results', 'snapshot-submit', 'preserve-submit', 'inspect-submit') else 'b06-statement-1'
    work, out = ROOT / 'build' / phase, ROOT / 'reports' / phase
    work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    private = work / 'private'; private.mkdir(mode=0o700, exist_ok=True); private.chmod(0o700)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
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
        target = out / 'logs' / stamp / raw.name
        if public:
            target.parent.mkdir(parents=True, exist_ok=True); target.write_text(safe)
        ledger = out / 'commands.json'; rows = json.loads(ledger.read_text()) if ledger.exists() else []
        rows.append({'action': args.action, 'name': name, 'argv': argv, 'exit_status': p.returncode,
                     'timestamp_utc': stamp, 'log': str((target if public else raw).relative_to(ROOT))})
        ledger.write_text(json.dumps(rows, indent=2) + '\n')
        print(name + ': exit ' + str(p.returncode), flush=True)
        if p.returncode:
            raise RuntimeError(name + ' failed; see fresh logs')
        return p.stdout

    def docker(name, *argv, **kw):
        return run(name, ['docker', *argv], **kw)

    def shell(name, code, public=True):
        text = docker(name, 'exec', '-i', SITE, 'python', 'manage.py', 'shell', stdin=code, public=public)
        return json.loads(text.split('JOURNEY_RESULT=', 1)[1])

    if args.action == 'inspect-submit':
        result = shell('native-ace-source-sync', "import json\nfrom pathlib import Path\nfrom django.contrib.staticfiles import finders\nfrom judge.models import Submission\np=Path(finders.find('django_ace/widget.js'))\nprint('JOURNEY_RESULT='+json.dumps({'source':p.read_text(),'native_submissions':Submission.objects.count()}))")
        (out / 'editor-inspection.json').write_text(json.dumps(result, indent=2) + '\n')
        return

    if args.action in ('snapshot-submit', 'preserve-submit'):
        assert json.loads((ROOT / 'reports/b06-statement-1/review.json').read_text())['status'] == 'PASS'
        mode = 'snapshot' if args.action == 'snapshot-submit' else 'preserve'
        result = shell('precise-' + args.action, 'MODE=' + repr(mode) + '\n' + (HERE / 'submission_state.py').read_text())
        (out / (args.action + '-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        return
    if args.action == 'instrument':
        assert json.loads((ROOT / 'reports/b06-statement-1/review.json').read_text())['status'] == 'PASS'
        os.environ['CPJ_SITE_REPORT_DIR'] = str(out)
        # Stop only idle worker/native services; preserve DB/Redis/web throughout.
        run('idle-worker-stop', [sys.executable, '-B', str(HERE / 'b03.py'), 'stop'])
        run('idle-bridge-stop', [sys.executable, '-B', str(HERE / 'b02.py'), 'stop'])
        result = shell('passive-native-request-observation', (HERE / 'bridge_observe.py').read_text())
        run('managed-observed-start', [sys.executable, '-B', str(HERE / 'manage.py'), 'start'])
        (out / 'observation.json').write_text(json.dumps(result, indent=2) + '\n')
        return
    if args.action == 'submit':
        assert json.loads((ROOT / 'reports/b06-statement-1/review.json').read_text())['status'] == 'PASS'
        guard = shell('browser-submit-preflight', "import json\nfrom judge.models import Submission,Problem,Judge\np=Problem.objects.get(code='pv000000000000000001')\nassert not Submission.objects.filter(problem=p).exists(), 'Inspect existing submission; never blindly repeat browser POST'\nassert Judge.objects.filter(online=True,problems=p,runtimes__key='CPP23').exists()\nprint('JOURNEY_RESULT='+json.dumps({'no_prior_submission':True,'native_worker_ready':True}))")
        output = work / 'browser' / stamp; output.mkdir(parents=True)
        try:
            docker('real-native-browser-submission', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}', '--network', 'host',
                   '--shm-size', '256m', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                   '--mount', f'type=bind,src={ROOT / "build/b01-site-1/private/accounts.json"},dst=/run/accounts.json,readonly',
                   '--mount', f'type=bind,src={HERE / "submission_browser.py"},dst=/tests/browser.py,readonly',
                   '--mount', f'type=bind,src={ROOT / "local-packages/gaming-grid.zip"},dst=/run/package.zip,readonly',
                   '--mount', f'type=bind,src={output},dst=/results', 'cpjudge-b01-browser:local1', 'python', '/tests/browser.py', public=False)
        finally:
            if (output / 'sessions.json').exists():
                keys = json.loads((output / 'sessions.json').read_text()); secrets.extend(keys)
                shell('cleanup-owned-browser-sessions', 'KEYS=' + repr(keys) + "\nimport importlib,json\nfrom django.conf import settings\nbackend=importlib.import_module(settings.SESSION_ENGINE)\nfor key in KEYS:\n store=backend.SessionStore(session_key=key);store.delete();assert store.load()=={}\nprint('JOURNEY_RESULT='+json.dumps({'owned_browser_sessions_deleted':len(KEYS)}))")
            if (output / 'submission-receipt.json').exists():
                receipt = json.loads((output / 'submission-receipt.json').read_text())
                (out / ('receipt-' + stamp + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
        result = json.loads((output / 'result.json').read_text())
        (out / ('browser-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        return
    if args.action == 'results':
        receipt = json.loads(sorted(out.glob('receipt-*.json'))[-1].read_text())
        sid = receipt['submission_id']
        result = shell('native-stored-submission-and-cases', 'MODE="results"\nSUBMISSION_ID=' + repr(sid) + '\n' + (HERE / 'submission_state.py').read_text())
        trace_text = docker('passive-actual-native-packet-trace', 'exec', SITE, 'cat', '/tmp/b07-native-trace.jsonl')
        trace = [json.loads(line) for line in trace_text.splitlines() if line.strip()]
        selected = [row for row in trace if row.get('submission-id') == sid]
        requests = [row for row in selected if row['name'] == 'submission-request' and row['direction'] == 'sent']
        assert len(requests) == 1
        request = requests[0]
        assert request['time-limit'] == 2.0 and request['memory-limit'] == 262144
        assert request['language'] == 'CPP23' and request['problem-id'] == CODE and request['short-circuit'] is False
        assert request['source_sha256'] == receipt['browser_form_post']['source_sha256'] == result['source_sha256']
        assert result['source_canonical_sha256'] == receipt['reference_source_sha256'] == receipt['browser_form_post']['source_canonical_sha256']
        assert result['status'] == 'D' and result['verdict'] == 'AC'
        assert len(result['cases']) == 103 and [case['case'] for case in result['cases']] == list(range(1, 104))
        assert all(case['status'] == 'AC' and case['points'] == case['total'] == 1 for case in result['cases'])
        assert result['case_points'] == result['case_total'] == result['points'] == 103
        assert result['judge'] == 'cpjudge-local-worker' and result['language'] == 'CPP23'
        assert not result['contest_attached'] and not result['pretests_only'] and not result['language_limits']
        assert any(row['name'] == 'grading-end' for row in selected)
        callback_cases = [case for row in selected if row['name'] == 'test-case-status' for case in row['cases']]
        assert len(callback_cases) == 103
        assert sorted(case['position'] for case in callback_cases) == list(range(1, 104))
        assert all(case['status'] == 0 and case['points'] == case['total-points'] == 1 for case in callback_cases)
        for callback, stored in zip(sorted(callback_cases, key=lambda c: c['position']), result['cases']):
            assert callback['position'] == stored['case']
            assert callback['time'] == stored['time'] and callback['memory'] == stored['memory']
            assert callback['points'] == stored['points'] and callback['total-points'] == stored['total']
        raw = docker('actual-worker-raw-log', 'logs', WORKER, public=False)
        lines = raw.splitlines()
        starts = [i for i, line in enumerate(lines) if 'Start grading ' + CODE + '/' + str(sid) + ' in CPP23' in line]
        ends = [i for i, line in enumerate(lines) if 'Done grading ' + CODE + '/' + str(sid) + '.' in line]
        assert len(starts) == len(ends) == 1 and starts[0] < ends[0]
        block = lines[starts[0]:ends[0]+1]
        summary = [line for line in block if any(token in line for token in ('Start grading ', 'Done grading ', 'Accept submission: ' + str(sid) + ':'))]
        matches = [re.search(r'Test case\s+(\d+)\s+([A-Z]+)\s+\[', line) for line in block]
        worker_cases = [(int(m.group(1)), m.group(2)) for m in matches if m]
        assert worker_cases == [(i, 'AC') for i in range(1, 104)]
        sanitized_worker_log = '\n'.join(line for line in block if line in summary or re.search(r'Test case\s+\d+\s+AC\s+\[', line)) + '\n'
        (out / 'native-worker-cases.log').write_text(sanitized_worker_log)
        if (out / 'worker-log-summary.json').exists():
            shutil.copy2(out / 'worker-log-summary.json', out / ('worker-log-summary-before-' + stamp + '.json'))
        (out / 'worker-log-summary.json').write_text(json.dumps({'raw_log_sha256': hashlib.sha256(raw.encode()).hexdigest(),
              'matched_submission_lines': summary, 'explicit_native_worker_AC_cases': len(worker_cases),
              'raw_private_log': str((work / 'logs' / stamp / 'actual-worker-raw-log.log').relative_to(ROOT))}, indent=2) + '\n')
        if result['error_present']:
            docker('retained-native-compiler-messages', 'exec', SITE, 'cat', '/tmp/b07-compiler-message.txt', public=False)
        result.update({'acceptance': 'PASS', 'actual_sent_request': request, 'native_callback_cases': len(callback_cases),
                       'browser_display_agrees': True, 'contest_standings': 'NOT TESTED'})
        (out / 'cases.json').write_text(json.dumps(result['cases'], indent=2) + '\n')
        (out / 'native-trace.json').write_text(json.dumps(selected, indent=2) + '\n')
        if (out / 'result.json').exists():
            shutil.copy2(out / 'result.json', out / ('result-before-' + stamp + '.json'))
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        return

    if args.action == 'inspect':
        result = shell('native-font-origin', "import json\nfrom pathlib import Path\nfrom django.contrib.staticfiles.finders import get_finders\nfound=[]\nfor finder in get_finders():\n for name,storage in finder.list([]):\n  if name.endswith(('.css','.js')):\n   p=Path(storage.path(name))\n   if p.is_file() and 'fonts.googleapis.com' in p.read_text(errors='replace'):found.append(name)\nprint('JOURNEY_RESULT='+json.dumps({'font_sources':found}))")
        (out / ('inspection-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        return

    if args.action == 'snapshot':
        result = shell('precise-initial-snapshot', 'MODE="snapshot"\n' + (HERE / 'journey_state.py').read_text())
        (out / ('snapshot-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        return
    if args.action == 'prepare':
        from defusedxml import ElementTree as ET
        package = ROOT / 'local-packages/gaming-grid.zip'
        assert hashlib.sha256(package.read_bytes()).hexdigest() == json.loads((ROOT / 'reports/b04-installation-1/mapping.json').read_text())['package_sha256']
        with zipfile.ZipFile(package) as archive:
            xml = ET.fromstring(archive.read('problem.xml'))
            statements = [e for e in xml.findall('statements/statement') if e.get('type') == 'text/html' and e.get('language') == 'english']
            assert len(statements) == 1
            path = Path(statements[0].get('path'))
            assert not path.is_absolute() and '..' not in path.parts
            payload = {'html': archive.read(str(path)).decode('utf-8'),
                       'css': archive.read(str(path.parent / 'problem-statement.css')).decode('utf-8')}
        code = 'PAYLOAD=' + repr(payload) + '\n' + (HERE / 'statement_prepare.py').read_text()
        docker('copy-sanitizer', 'cp', str(HERE / 'statement_sanitize.py'), SITE + ':/tmp/b06_statement_sanitize.py')
        result = shell('strict-presentation-prepare', code)
        (out / 'presentation.json').write_text(json.dumps(result, indent=2) + '\n')
        return
    if args.action == 'install':
        result = shell('native-description-and-scoped-grant', (HERE / 'statement_install.py').read_text())
        docker('install-private-asset-view', 'cp', str(HERE / 'imported_statement_view.py'), SITE + ':/app/judge/views/imported_statement.py')
        docker('install-receipt-bound-filter', 'cp', str(HERE / 'imported_statement_filter.py'), SITE + ':/app/judge/jinja2/imported_statement.py')
        patch = (HERE / 'statement_overlay.py').read_text()
        result.update(shell('bounded-native-template-route', patch))
        # Reload only web process. Existing bridge/Celery/events/worker remain active.
        docker('reload-web-only', 'exec', '-i', SITE, 'python', stdin="import os,signal\nfrom pathlib import Path\nfor p in Path('/proc').iterdir():\n if not p.name.isdigit():continue\n try:a=(p/'cmdline').read_bytes().split(bytes([0]))\n except OSError:continue\n if a[1:3]==[b'manage.py',b'runserver']:os.kill(int(p.name),signal.SIGTERM)\n")
        docker('start-preserved-web', 'exec', '-d', SITE, 'sh', '-c', 'exec python manage.py runserver 0.0.0.0:8000 --noreload > /tmp/b06-http.log 2>&1')
        (out / ('installation-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        return
    if args.action == 'browser':
        output = work / 'browser' / stamp; output.mkdir(parents=True)
        try:
            docker('real-statement-browser', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}', '--network', 'host',
                   '--shm-size', '256m', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                   '--mount', f'type=bind,src={ROOT / "build/b01-site-1/private/accounts.json"},dst=/run/accounts.json,readonly',
                   '--mount', f'type=bind,src={HERE / "statement_browser.py"},dst=/tests/browser.py,readonly',
                   '--mount', f'type=bind,src={ROOT / "local-packages/gaming-grid.zip"},dst=/run/package.zip,readonly',
                   '--mount', f'type=bind,src={output},dst=/results', 'cpjudge-b01-browser:local1', 'python', '/tests/browser.py', public=False)
        finally:
            if (output / 'sessions.json').exists():
                keys = json.loads((output / 'sessions.json').read_text())
                secrets.extend(keys)
                shell('cleanup-owned-browser-sessions', 'KEYS=' + repr(keys) + "\nimport importlib,json\nfrom django.conf import settings\nbackend=importlib.import_module(settings.SESSION_ENGINE)\nfor key in KEYS:\n store=backend.SessionStore(session_key=key);store.delete();assert store.load()=={}\nprint('JOURNEY_RESULT='+json.dumps({'owned_browser_sessions_deleted':len(KEYS)}))")
        result = json.loads((output / 'result.json').read_text())
        (out / ('browser-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        return
    if args.action == 'preserve':
        result = shell('precise-preservation', 'MODE="preserve"\n' + (HERE / 'journey_state.py').read_text())
        (out / ('preservation-' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        return
    raise RuntimeError('B07 must follow completed B06 evidence/review')


if __name__ == '__main__':
    main()
