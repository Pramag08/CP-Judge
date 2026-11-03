"""Pinned-source audit and bounded native path/selection semantics; no judging."""
import ast
import glob
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple
from fnmatch import fnmatch

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SITE = ROOT / 'build/a09-site-1/site'
WORKER = Path('/tmp/cp-judge-dmoj')
PINS = {'site': '604d60cfd764bc708b04ffd75b715a5398b91f8b',
        'worker': '1245dc4158dbb9e906c4c103e1ea939e012ee79b'}
FILES = {
    'site': ['judge/models/problem.py', 'judge/models/submission.py', 'judge/models/contest.py',
             'judge/judgeapi.py', 'judge/bridge/django_handler.py', 'judge/bridge/judge_list.py',
             'judge/bridge/judge_handler.py'],
    'worker': ['dmoj/judgeenv.py', 'dmoj/judge.py', 'dmoj/packet.py', 'dmoj/problem.py',
               'dmoj/monitor.py', 'dmoj/control.py', 'dmoj/checkers/bridged.py',
               'dmoj/utils/helper_files.py', 'dmoj/executors/compiled_executor.py',
               'dmoj/executors/c_like_executor.py'],
}
commands = []
sources = {}
for label, checkout in [('site', SITE), ('worker', WORKER)]:
    args = ['git', '-C', str(checkout), 'rev-parse', 'HEAD']
    p = subprocess.run(args, capture_output=True, text=True)
    commands.append({'argv': args, 'exit_status': p.returncode})
    assert p.returncode == 0 and p.stdout.strip() == PINS[label]
    for filename in FILES[label]:
        path = checkout / filename
        args = ['git', '-C', str(checkout), 'show', PINS[label] + ':' + filename]
        p = subprocess.run(args, capture_output=True)
        commands.append({'argv': args, 'exit_status': p.returncode})
        assert p.returncode == 0 and p.stdout == path.read_bytes(), filename
        sources[label + '/' + filename] = hashlib.sha256(p.stdout).hexdigest()

env_source = WORKER / 'dmoj/judgeenv.py'
tree = ast.parse(env_source.read_text())
names = {'get_problem_root', 'get_problem_roots', 'clear_problem_dirs_cache',
         'get_supported_problems_and_mtimes'}
functions = [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name in names]
assert len(functions) == 4
ns = dict(os=os, glob=glob, fnmatch=fnmatch, Dict=Dict, List=List, Optional=Optional,
          Tuple=Tuple, utf8text=lambda x: x, print_ansi=lambda *x: None,
          startup_warnings=[], _problem_root_cache={}, _problem_dirs_cache=None)
exec(compile(ast.Module(body=functions, type_ignores=[]), str(env_source), 'exec'), ns)
observed = {}
with tempfile.TemporaryDirectory(prefix='native-', dir=ROOT / 'build/a11-dispatch-1') as td:
    a, b = Path(td) / 'a', Path(td) / 'b'
    for root in (a, b):
        (root / 'pv1').mkdir(parents=True)
        (root / 'pv1/init.yml').write_text('test_cases: []\n')
    ns['problem_globs'] = [str(a / '*/'), str(b / '*/')]
    assert ns['get_problem_root']('pv1') == str(a / 'pv1')
    observed['duplicate_code_first_root_wins'] = True
    ns['problem_globs'] = [str(b / '*/'), str(a / '*/')]
    ns['clear_problem_dirs_cache']()
    assert ns['get_problem_root']('pv1') == str(a / 'pv1')
    observed['root_cache_survives_directory_cache_clear'] = True
    before = ns['get_supported_problems_and_mtimes']()
    original = (b / 'pv1').stat()
    (b / 'pv1/init.yml').write_text('test_cases: [changed]\n')
    os.utime(b / 'pv1', ns=(original.st_atime_ns, original.st_mtime_ns))
    after = ns['get_supported_problems_and_mtimes']()
    assert before == after
    observed['advertisement_not_a_content_hash'] = True
    (b / 'pv2').mkdir()
    (b / 'pv2/init.yml').write_text('test_cases: []\n')
    assert 'pv2' in dict(ns['get_supported_problems_and_mtimes']())
    observed['new_immutable_code_advertised'] = True

handler = SITE / 'judge/bridge/judge_handler.py'
cls = next(x for x in ast.parse(handler.read_text()).body if isinstance(x, ast.ClassDef) and x.name == 'JudgeHandler')
method = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == 'can_judge')
scope = {}
exec(compile(ast.Module(body=[method], type_ignores=[]), str(handler), 'exec'), scope)
judge = SimpleNamespace(problems={'pv1': 0}, executors={'CPP23': []}, is_disabled=False, name='j1')
check = scope['can_judge']
assert check(judge, 'pv1', 'CPP23')
assert not check(judge, 'pv2', 'CPP23')
assert not check(judge, 'pv1', 'CPP17')
assert not check(judge, 'pv1', 'CPP23', 'j2')
judge.is_disabled = True
assert not check(judge, 'pv1', 'CPP23')
assert check(judge, 'pv1', 'CPP23', 'j1')
observed['can_judge_code_executor_and_target_cases'] = 6
observed['explicit_target_bypasses_handler_disabled_check'] = True
result = {'status': 'PASS', 'scope': 'source identity + isolated native function semantics',
          'pins': PINS, 'source_sha256': sources, 'observations': observed,
          'website_bridge_worker_compatibility': 'NOT TESTED', 'actual_judging': 'NOT RUN',
          'conversion': 'NOT RUN', 'source_modified': False}
(OUT / 'evidence.json').write_text(json.dumps(result, indent=2) + '\n')
commands.insert(0, {'argv': ['python3', '-B', 'reports/a11-dispatch-1/inspect.py'], 'exit_status': 0})
(OUT / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
print('PASS: pinned sources; 4 path/advertisement observations and 6 can_judge cases; no judging or live bridge.')
