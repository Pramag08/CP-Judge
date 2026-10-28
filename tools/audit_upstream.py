"""Read-only audit of the original Polygon reader and unadapted DMOJ writer."""
import argparse
import dataclasses
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from compat.convert import upstream, extract, read
from tools.make_fixtures import build

p = argparse.ArgumentParser()
p.add_argument('polygon2hydro_checkout', type=Path)
a = p.parse_args()
commit = subprocess.check_output(['git', '-C', str(a.polygon2hydro_checkout), 'rev-parse', 'HEAD'], text=True).strip()
assert commit == '93aca21db49131baa0ca3077d6fec037ac52b5e6'
sys.path.insert(0, str(a.polygon2hydro_checkout / 'src'))
from p2h.polygon_reader import read_problem
from p2h.hydro_writer import _build_config_yaml

writer, ir = upstream()
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    build(root / 'fixtures')
    extract(root / 'fixtures/groups.zip', root / 'problems/groups')
    problem = read_problem(root, 'groups')
    print('Polygon reader commit:', commit)
    print('Polygon reader:', len(problem.tests), 'tests,', problem.time_ms, 'ms,', problem.memory_mb, 'MiB')
    print('Reader group/scoring/dependency fields:', [f.name for f in dataclasses.fields(problem) if any(s in f.name for s in ['group', 'scor', 'depend'])])
    print('Hydro scoring config:')
    print(_build_config_yaml(problem.time_ms, problem.memory_mb, test_files=[('1.in', '1.out')], is_interactive=False, interactor_name=None, checker_name='checker.cpp'))
    problem, manifest = read(root / 'problems/groups', ir)
    out = root / 'output'
    out.mkdir()
    writer.write_dmoj(ir.ProblemBundle('polygon', [problem]), out, {})
    with zipfile.ZipFile(out / 'groups.zip') as z:
        print('Unadapted DMOJ init:')
        print(z.read('init.yml').decode())
print('This audit did not run generators, checkers or submissions.')
