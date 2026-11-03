"""Read-only worker byte/configuration checks; no compile, checker or submission."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import yaml
from dmoj import judgeenv

code = REQUEST['native_code']
sys.argv = ['b05-installed-verifier', '-c', '/config.yml', '--no-ansi']
judgeenv.load_env(cli=True)
root = Path(judgeenv.get_problem_root(code))
assert root == Path('/problems') / code
assert code in judgeenv.get_supported_problems()
assert sum(p.name == code for p in Path('/problems').glob('*') if p.is_dir()) == 1
files = []
for path in sorted(root.rglob('*')):
    assert not path.is_symlink()
    if path.is_file():
        assert path.stat().st_mode & 0o222 == 0
        files.append({'path': path.relative_to(root).as_posix(), 'size': path.stat().st_size,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
assert files == FILES
conf = yaml.safe_load((root / 'init.yml').read_text())
assert len(conf['test_cases']) == 103
assert conf['checker'] == REQUEST['checker'] and conf['checker']['args']['lang'] == 'CPP23'
for name in ('time_limit', 'memory_limit', 'short_circuit'):
    assert conf[name] == REQUEST['site_values'][name]
with zipfile.ZipFile(root / 'data.zip') as archive:
    assert len(archive.namelist()) == 206
    for i, (case, hashes) in enumerate(zip(conf['test_cases'], CASE_HASHES), 1):
        assert case == {'in': f'{i}.in', 'out': f'{i}.out', 'points': 1}
        assert hashlib.sha256(archive.read(case['in'])).hexdigest() == hashes['input']
        assert hashlib.sha256(archive.read(case['out'])).hexdigest() == hashes['answer']
assert len(CASE_HASHES) == 103
assert not (root / 'solutions').exists()
print(json.dumps({'status': 'PASS', 'input_output_pairs': 103, 'archive_entries': 206,
      'all_installed_file_hashes_match': True, 'checker_header_samples_assets_exact': True,
      'ordered_active_cases': 103, 'case_points_total': 103, 'checker_language': 'CPP23',
      'source_time_ms': REQUEST['source_time_ms'], 'source_memory_bytes': REQUEST['source_memory_bytes'],
      'time_seconds': conf['time_limit'], 'memory_KiB': conf['memory_limit'],
      'native_root_unique': True, 'reference_source_installed': False, 'judging': 'NOT TESTED'}, indent=2))
