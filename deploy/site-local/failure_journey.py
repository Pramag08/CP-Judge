"""B08/B09 real browser probes, reusing B07's driver and read-only collector."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import grp
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
WORK = ROOT / 'build/b08-b09-probes-1'
OUT = ROOT / 'reports/b08-b09-probes-1'
SITE = 'cpjudge-b01-site'
WORKER = 'cpjudge-b03-worker'
ACTION = sys.argv[1]
assert ACTION in ('snapshot', 'wrong_answer', 'compile_error', 'runtime', 'timeout', 'preserve')
if grp.getgrnam('docker').gr_gid not in [os.getgid(), *os.getgroups()]:
    os.execvp('sg', ['sg', 'docker', '-c', shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), ACTION])])
WORK.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
private = WORK / (ACTION + '-' + stamp)
private.mkdir(mode=0o700)

def run(name, argv, stdin=None):
    p = subprocess.run(argv, input=stdin, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = private / (name + '.log')
    log.write_text(p.stdout); log.chmod(0o600)
    ledger = OUT / 'commands.json'
    rows = json.loads(ledger.read_text()) if ledger.exists() else []
    rows.append({'action': ACTION, 'command': argv, 'exit_status': p.returncode, 'log': str(log.relative_to(ROOT))})
    ledger.write_text(json.dumps(rows, indent=2) + '\n')
    print(name + ': exit ' + str(p.returncode), flush=True)
    assert p.returncode == 0, log
    return p.stdout

def docker(name, *argv, **kw):
    return run(name, ['docker', *argv], **kw)

def shell(name, code):
    value = docker(name, 'exec', '-i', SITE, 'python', 'manage.py', 'shell', stdin=code)
    return json.loads(value.split('JOURNEY_RESULT=', 1)[1])

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

state = (HERE / 'submission_state.py').read_text()
snapshot_args = "SNAPSHOT_PATH='/tmp/b08-b09-before.json'\nALLOW_PRIOR=True\n"
if ACTION in ('snapshot', 'preserve'):
    # Exact immutable files plus container/config identity, without publishing secrets.
    config = {}
    for name in (SITE, WORKER):
        data = json.loads(docker('inspect-' + name, 'inspect', name))[0]
        config[name] = {'image': data['Image'], 'config_sha256': hashlib.sha256(json.dumps({k: data[k] for k in ('Config', 'HostConfig', 'Mounts')}, sort_keys=True).encode()).hexdigest()}
    from tools.site_problem import file_manifest
    installed = ROOT / 'build/b05-problem-1/problems/pv000000000000000001'
    # Resolve the actual installation from the owned worker's read-only mount.
    data = json.loads((private / ('inspect-' + WORKER + '.log')).read_text())[0]
    mount = next(m for m in data['Mounts'] if m['Destination'] == '/problems')
    assert not mount['RW']
    config['installed_files'] = file_manifest(Path(mount['Source']) / 'pv000000000000000001')
    baseline = WORK / 'configuration-before.json'
    if ACTION == 'snapshot':
        assert not baseline.exists()
        baseline.write_text(json.dumps(config, sort_keys=True))
    else:
        assert config == json.loads(baseline.read_text())
    mode = 'snapshot' if ACTION == 'snapshot' else 'preserve'
    result = shell(ACTION, snapshot_args + 'MODE=' + repr(mode) + "\nEXPECTED_NEW={'judge.submission':4,'judge.submissionsource':4,'judge.submissiontestcase':309}\n" + state)
    result['immutable_problem_files_container_images_configuration_preserved'] = True
    save(ACTION + '.json', result)
    sys.exit(0)

source_dir = ROOT / 'build/a03-judge-1/pipeline/problems/gaming-grid'
tests = {t['label']: t for t in yaml.safe_load((source_dir / 'init.yml').read_text())['tests']}
if ACTION == 'compile_error':
    source = 'int main( {\n'  # No historical CE probe existed; intentionally invalid syntax.
    verdict, long_verdict, cases = 'CE', 'Compile Error', []
else:
    test = tests[ACTION]
    source = (source_dir / test['source']).read_text()
    verdict, long_verdict = {'wrong_answer': ('WA', 'Wrong Answer'), 'runtime': ('RTE', 'Runtime Error'), 'timeout': ('TLE', 'Time Limit Exceeded')}[ACTION]
    cases = [test['cases'][i] for i in range(1, 104)] if 'cases' in test else [test['expect']] * 103
probe = {'verdict': verdict, 'long_verdict': long_verdict, 'cases': cases, 'score': str(cases.count('AC')) + '/103'}
receipt_file = OUT / (ACTION + '-receipt.json')
resume = json.loads(receipt_file.read_text()) if receipt_file.exists() else None
guard = shell('preflight', "import json\nfrom judge.models import Submission,Problem,Judge\np=Problem.objects.get(code='pv000000000000000001')\nassert not Submission.objects.filter(status__in=Submission.IN_PROGRESS_GRADING_STATUS).exists()\nassert Judge.objects.filter(online=True,problems=p,runtimes__key='CPP23').exists()\nprint('JOURNEY_RESULT='+json.dumps({'prior_ids':list(Submission.objects.values_list('id',flat=True))}))")
(private / 'probe.cpp').write_text(source)
(private / 'probe.json').write_text(json.dumps(probe))
saved_browser = sorted(p for p in WORK.glob(ACTION + '-*') if (p / 'result.json').exists()) if resume else []
browser_output = saved_browser[-1] if saved_browser else private
if saved_browser:
    receipt = resume
else:
    try:
        docker('browser', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}', '--network', 'host', '--shm-size', '256m', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--mount', f'type=bind,src={ROOT / "build/b01-site-1/private/accounts.json"},dst=/run/accounts.json,readonly',
               '--mount', f'type=bind,src={HERE / "submission_browser.py"},dst=/tests/browser.py,readonly',
               '--mount', f'type=bind,src={private / "probe.cpp"},dst=/run/probe.cpp,readonly',
               '--mount', f'type=bind,src={private / "probe.json"},dst=/run/probe.json,readonly',
               '--mount', f'type=bind,src={private},dst=/results',
               *(['--mount', f'type=bind,src={receipt_file},dst=/run/receipt.json,readonly'] if resume else []),
               'cpjudge-b01-browser:local1', 'python', '/tests/browser.py')
    finally:
        if (private / 'submission-receipt.json').exists():
            receipt = json.loads((private / 'submission-receipt.json').read_text())
            save(ACTION + '-receipt.json', receipt)
        if (private / 'sessions.json').exists():
            keys = json.loads((private / 'sessions.json').read_text())
            shell('cleanup-browser-sessions', 'KEYS=' + repr(keys) + "\nimport importlib,json\nfrom django.conf import settings\nb=importlib.import_module(settings.SESSION_ENGINE)\nfor key in KEYS:\n s=b.SessionStore(session_key=key);s.delete();assert s.load()=={}\nprint('JOURNEY_RESULT='+json.dumps({'deleted':len(KEYS)}))")
sid = receipt['submission_id']
assert (sid in guard['prior_ids']) if resume else (sid not in guard['prior_ids'])
browser = json.loads((browser_output / 'result.json').read_text())
result = shell('stored-results', 'MODE="results"\nSUBMISSION_ID=' + str(sid) + '\n' + state)
trace = [json.loads(line) for line in docker('passive-trace', 'exec', SITE, 'cat', '/tmp/b07-native-trace.jsonl').splitlines()]
trace = [row for row in trace if row.get('submission-id') == sid]
requests = [row for row in trace if row['name'] == 'submission-request']
assert len(requests) == 1
request = requests[0]
assert request['time-limit'] == 2 and request['memory-limit'] == 262144 and request['short-circuit'] is False
assert request['language'] == 'CPP23' and request['problem-id'] == 'pv000000000000000001'
assert request['source_sha256'] == result['source_sha256'] == hashlib.sha256(source.replace('\n', '\r\n').strip().encode()).hexdigest()
assert receipt['browser_form_post']['source_sha256'] == hashlib.sha256(source.replace('\n', '\r\n').encode()).hexdigest()
assert hashlib.sha256(source.strip().encode()).hexdigest() == result['source_canonical_sha256'] == receipt['browser_form_post']['source_canonical_sha256']
assert result['verdict'] == browser['displayed_verdict'] == verdict
assert result['status'] == ('CE' if verdict == 'CE' else 'D')
assert result['judge'] == 'cpjudge-local-worker' and result['language'] == 'CPP23'
assert not result['contest_attached'] and not result['pretests_only'] and not result['language_limits']
assert [c['status'] for c in result['cases']] == cases == browser['displayed_cases']
callbacks = sorted([c for row in trace if row['name'] == 'test-case-status' for c in row['cases']], key=lambda c:c['position'])
assert len(callbacks) == len(cases)
# Match pinned native JudgeHandler precedence; flags can contain several bits.
def native_verdict(status):
    return next((name for bit, name in ((4,'TLE'),(8,'MLE'),(64,'OLE'),(2,'RTE'),(16,'IR'),(1,'WA'),(32,'SC')) if status & bit), 'AC')
for i, (cb, stored, expected) in enumerate(zip(callbacks, result['cases'], cases), 1):
    assert cb['position'] == stored['case'] == browser['displayed_case_numbers'][i-1] == i
    assert native_verdict(cb['status']) == expected
    assert cb['points'] == stored['points'] == int(expected == 'AC')
    assert cb['total-points'] == stored['total'] == 1
    assert cb['time'] == stored['time'] and cb['memory'] == stored['memory']
assert any(row['name'] == ('compile-error' if verdict == 'CE' else 'grading-end') for row in trace)
if verdict != 'CE':
    assert result['case_points'] == result['points'] == cases.count('AC') and result['case_total'] == 103
else:
    assert result['error_present'] and not result['cases']
    docker('compiler-error-private', 'exec', SITE, 'cat', '/tmp/b07-compiler-message.txt')
raw = docker('worker-private', 'logs', WORKER)
lines = raw.splitlines()
start = next(i for i,line in enumerate(lines) if f'Start grading pv000000000000000001/{sid} in CPP23' in line)
end = next(i for i,line in enumerate(lines[start:],start) if f'Done grading pv000000000000000001/{sid}.' in line)
block = lines[start:end+1]
worker_cases = [(int(m.group(1)),m.group(2)) for line in block if (m:=re.search(r'Test case\s+(\d+)\s+([A-Z]+)\s+\[',line))]
assert worker_cases == list(enumerate(cases,1)), worker_cases
if verdict == 'CE':
    assert any('Failed compiling submission!' in line for line in block)
safe = [line for line in block if re.search(r'Test case\s+\d+\s+[A-Z]+\s+\[',line) or 'Start grading ' in line or 'Done grading ' in line or 'Failed compiling submission!' in line]
(OUT / (ACTION + '-worker.log')).write_text('\n'.join(safe)+'\n')
result.update({'acceptance':'PASS','expected_verdict':verdict,'browser':browser,'request':request,'trace':trace,
               'executed_cases':len(cases),'passed_cases':cases.count('AC'),'skipped_cases':0,
               'unexecuted_cases':103-len(cases),'first_failed_case':next((i for i,c in enumerate(cases,1) if c!='AC'),None),
               'browser_read_only_resume':bool(resume),'worker_case_count':len(worker_cases),'raw_evidence':str(private.relative_to(ROOT)), 'browser_evidence':str(browser_output.relative_to(ROOT))})
save(ACTION + '-result.json', result)
print(f'PASS: submission {sid}, {verdict}, {len(cases)} actual cases',flush=True)
