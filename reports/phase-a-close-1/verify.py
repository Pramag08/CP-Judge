"""Read-only contract/source/dependency audit; writes only new run reports.
No application, database, conversion or judge execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'build/phase-a-close-1'
CONTRACTS = {
    'A06': 'permissions.md', 'A07': 'contest-rules.md',
    'A08': None, 'A10': 'contest-native-mapping.md',
    'A11': 'problem-version-dispatch.md', 'A12': 'custom-input-run.md',
}
SHARED = {'AGENTS.md', 'PROJECT_STATUS.md', 'SecureExam-Implementation-Plan.md', 'MVP_DEPENDENCIES.md'}


def rows(text):
    return {p[0]: p for line in text.splitlines()
            if re.match(r'^\| [A-H]\d{2} \|', line)
            for p in [[v.strip() for v in line.split('|')[1:-1]]]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=[*CONTRACTS, 'final'], required=True)
    args = parser.parse_args()
    command = f'python3 -B reports/phase-a-close-1/verify.py --task {args.task}'
    plan = (ROOT / 'SecureExam-Implementation-Plan.md').read_text()
    current = rows(plan)
    previous = rows((BASE / 'SecureExam-Implementation-Plan.md').read_text())
    assert len(current) == 112 and current.keys() == previous.keys()
    historical = ['A01', 'A02', 'A03', 'A04', 'A05', 'A09']
    for task in historical:
        assert current[task] == previous[task], ('changed historical milestone', task)
    edges = {k: set(re.findall(r'\b[A-H]\d{2}\b', v[2])) for k, v in current.items()}
    visiting, visited = set(), set()
    def visit(task):
        assert task not in visiting, ('cycle', task)
        if task in visited:
            return
        visiting.add(task)
        for dep in edges[task]:
            assert dep in current
            visit(dep)
        visiting.remove(task)
        visited.add(task)
    for task in current:
        visit(task)
    selected = set()
    def collect(task):
        if task in selected:
            return
        selected.add(task)
        for dep in edges[task]:
            collect(dep)
    collect('H05')
    assert len(selected) == 90, len(selected)
    assert 'C15' not in selected and 'C16' in selected and 'C17' in selected
    assert all(not current[t][3].startswith('DEFERRED') for t in selected)
    paths = [ROOT / name for name in SHARED]
    tasks = list(CONTRACTS) if args.task == 'final' else [args.task]
    for task in tasks:
        if CONTRACTS[task]:
            path = ROOT / 'docs/contracts' / CONTRACTS[task]
            assert path.is_file() and len(path.read_text()) > 1000
            paths.append(path)
        if args.task == 'final':
            assert 'COMPLETE' in current[task][3], task
    link_count = 0
    for path in paths:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            assert (path.parent / target.split('#', 1)[0]).exists(), (str(path), target)
            link_count += 1
    before = json.loads((BASE / 'before-files.json').read_text())
    changed = []
    for filename, digest in before.items():
        path = ROOT / filename
        assert path.is_file(), ('removed', filename)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            changed.append(filename)
    assert set(changed) <= SHARED, changed
    source_files = ['judge/models/contest.py', 'judge/models/problem.py',
                    'judge/models/submission.py', 'judge/views/user.py',
                    'judge/views/submission.py', 'dmoj/settings.py']
    source = ROOT / 'build/a09-site-1/site'
    pin = '604d60cfd764bc708b04ffd75b715a5398b91f8b'
    hashes = {}
    for name in source_files:
        original = subprocess.run(['git', '-C', str(source), 'show', f'{pin}:{name}'],
                                  capture_output=True, check=True).stdout
        data = (source / name).read_bytes()
        assert data == original, name
        hashes[name] = hashlib.sha256(data).hexdigest()
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout + diff.stderr
    report = {
        'task': args.task, 'status': 'PASS', 'command': command, 'exit_status': 0,
        'scope': 'contract/documentation/source-identity audit, not runtime enforcement',
        'historical_completed_rows_preserved': historical,
        'backlog_rows': len(current), 'selected_mvp_dependency_closure': len(selected),
        'acyclic_and_no_deferred_prerequisites': True, 'local_links_checked': link_count,
        'baseline_files_checked': len(before), 'baseline_files_changed': sorted(changed),
        'previous_evidence_pins_and_application_bytes_preserved': True,
        'source_git_show_commands_exit_status': 0, 'site_pin': pin,
        'inspected_source_sha256': hashes, 'git_diff_check_exit_status': diff.returncode,
        'application_database_browser_tests': 'NOT RUN', 'conversion': 'NOT RUN',
        'actual_judging': 'NOT RUN', 'website_to_worker': 'NOT TESTED',
    }
    suffix = ''
    index = 1
    while (BASE / f'after-{args.task}{suffix}').exists():
        index += 1
        suffix = f'-{index}'
    (OUT / f'checks-{args.task}{suffix}.json').write_text(json.dumps(report, indent=2) + '\n')
    snapshot = BASE / f'after-{args.task}{suffix}'
    snapshot.mkdir(exist_ok=False)
    for name in SHARED:
        (snapshot / name).write_bytes((ROOT / name).read_bytes())
    print(f'PASS {args.task}: links/dependencies/source identity/preservation; no application or judging test.')

if __name__ == '__main__':
    main()
