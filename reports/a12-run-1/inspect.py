"""Inspect selected native Run extension points without compiling or executing code."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
WORKER = Path('/tmp/cp-judge-dmoj')
SITE = ROOT / 'build/a09-site-1/site'
PINS = {'site': '604d60cfd764bc708b04ffd75b715a5398b91f8b',
        'worker': '1245dc4158dbb9e906c4c103e1ea939e012ee79b'}
FILES = {'site': ['judge/judgeapi.py', 'judge/bridge/django_handler.py'],
         'worker': ['dmoj/packet.py', 'dmoj/control.py', 'dmoj/judge.py',
                    'dmoj/commands/submit.py', 'dmoj/graders/standard.py',
                    'dmoj/executors/base_executor.py', 'dmoj/executors/compiled_executor.py',
                    'dmoj/utils/communicate.py', 'dmoj/error.py']}
commands, hashes = [], {}
for label, checkout in [('site', SITE), ('worker', WORKER)]:
    args = ['git', '-C', str(checkout), 'rev-parse', 'HEAD']
    p = subprocess.run(args, capture_output=True, text=True)
    commands.append({'argv': args, 'exit_status': p.returncode})
    assert p.returncode == 0 and p.stdout.strip() == PINS[label]
    for filename in FILES[label]:
        args = ['git', '-C', str(checkout), 'show', PINS[label] + ':' + filename]
        p = subprocess.run(args, capture_output=True)
        commands.append({'argv': args, 'exit_status': p.returncode})
        assert p.returncode == 0 and p.stdout == (checkout / filename).read_bytes()
        hashes[label + '/' + filename] = hashlib.sha256(p.stdout).hexdigest()

def method(path, class_name, method_name):
    cls = next(x for x in ast.parse(path.read_text()).body if isinstance(x, ast.ClassDef) and x.name == class_name)
    return next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == method_name)

packet_path = WORKER / 'dmoj/packet.py'
receiver = method(packet_path, 'PacketManager', '_receive_packet')
packet_names = sorted({x.value for x in ast.walk(receiver)
                       if isinstance(x, ast.Constant) and isinstance(x.value, str) and x.value in
                       {'ping', 'get-current-submission', 'submission-request', 'terminate-submission', 'disconnect'}})
assert len(packet_names) == 5
errors = []
scope = {'log': SimpleNamespace(error=lambda *args: errors.append(args))}
exec(compile(ast.Module(body=[receiver], type_ignores=[]), str(packet_path), 'exec'), scope)
scope['_receive_packet'](SimpleNamespace(), {'name': 'custom-input-run', 'stdin': 'probe'})
assert len(errors) == 1 and errors[0][1] == 'custom-input-run'

control_path = WORKER / 'dmoj/control.py'
post = method(control_path, 'JudgeControlRequestHandler', 'do_POST')
scope = {}
exec(compile(ast.Module(body=[post], type_ignores=[]), str(control_path), 'exec'), scope)
statuses = []
scope['do_POST'](SimpleNamespace(path='/run', send_error=statuses.append))
assert statuses == [404]

base = ast.parse((WORKER / 'dmoj/executors/base_executor.py').read_text())
launch = method(WORKER / 'dmoj/executors/base_executor.py', 'BaseExecutor', 'launch')
traced = next(x for x in ast.walk(launch) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'TracedPopen')
kwargs = sorted(x.arg for x in traced.keywords)
assert {'security', 'time', 'wall_time', 'memory', 'stdin', 'stdout', 'stderr', 'nproc', 'fsize'} <= set(kwargs)
result = {'status': 'PASS', 'scope': 'source identity, AST inspection and isolated unsupported-route checks',
          'pins': PINS, 'source_sha256': hashes, 'native_receive_packet_names': packet_names,
          'unknown_custom_input_packet': 'logged unknown; no dispatch', 'control_post_run': 404,
          'native_TracedPopen_arguments': kwargs, 'custom_runner_implemented': False,
          'actual_custom_input_execution': 'NOT RUN', 'sandbox_compatibility': 'NOT TESTED',
          'official_judging': 'NOT RUN', 'source_modified': False}
(OUT / 'evidence.json').write_text(json.dumps(result, indent=2) + '\n')
commands.insert(0, {'argv': ['python3', '-B', 'reports/a12-run-1/inspect.py'], 'exit_status': 0})
(OUT / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
print('PASS: pinned source/launch APIs; native custom packet unsupported and control /run returns 404. No participant code execution.')
