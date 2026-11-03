"""Validate the CPJudge scope revision without running application tests."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'checks.json'
BEFORE = ROOT / 'build/cpjudge-scope-1'
PLAN = ROOT / 'SecureExam-Implementation-Plan.md'
DOCS = [PLAN, ROOT / 'MVP_DEPENDENCIES.md', ROOT / 'PROJECT_STATUS.md']


def task_rows(text):
    rows = {}
    for line in text.splitlines():
        if re.match(r'^\| [A-H]\d{2} \|', line):
            parts = [value.strip() for value in line.split('|')[1:-1]]
            assert len(parts) == 4, line
            assert parts[0] not in rows, parts[0]
            rows[parts[0]] = parts
    return rows


def series(letter, start, end):
    return {f'{letter}{i:02}' for i in range(start, end + 1)}


rows = task_rows(PLAN.read_text())
old_rows = task_rows((BEFORE / PLAN.name).read_text())
assert set(old_rows) <= set(rows), 'removed backlog IDs'
assert len(rows) == 112
completed = ['A01', 'A02', 'A03', 'A04', 'A05', 'A09']
for task in completed:
    assert rows[task] == old_rows[task], ('changed completed milestone', task)
for task in ('A06', 'A07', 'C15', 'C16', 'C17', 'E17'):
    assert 'NOT STARTED' in rows[task][3], task
deferred = series('F', 1, 7) | {'F09', 'F12'}
for task in deferred:
    assert 'DEFERRED' in rows[task][3] and 'COMPLETE' not in rows[task][3], task
selected = (
    series('A', 1, 12) | series('B', 1, 12) |
    series('C', 1, 13) | series('C', 15, 17) |
    series('D', 1, 14) | series('E', 1, 15) |
    {'E17', 'F08', 'F10', 'F11', 'F13', 'F14',
     'G01', 'G02', 'G03', 'G04', 'G06', 'G07', 'G08',
     'G10', 'G12', 'G13', 'G16'} | series('H', 1, 5)
)
assert len(selected) == 91 and not selected & deferred
edges = {task: set(re.findall(r'\b[A-H]\d{2}\b', row[2])) for task, row in rows.items()}
assert not set().union(*edges.values()) - set(rows), 'unknown task dependency'
assert not {task: edges[task] - selected for task in selected if edges[task] - selected}, 'MVP depends on optional/deferred work'
visiting, visited = set(), set()


def visit(task):
    assert task not in visiting, 'dependency cycle: ' + task
    if task in visited:
        return
    visiting.add(task)
    for dependency in edges[task]:
        visit(dependency)
    visiting.remove(task)
    visited.add(task)


for task in rows:
    visit(task)
ancestors = set()


def collect(task):
    if task in ancestors:
        return
    ancestors.add(task)
    for dependency in edges[task]:
        collect(dependency)


collect('H05')
assert ancestors == selected, 'release gate differs from selected MVP dependency closure'
for path in DOCS:
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if target.startswith(('https://', 'http://', '#', 'mailto:')):
            continue
        target_path = path.parent / target.split('#', 1)[0]
        assert target_path == OUT or target_path.exists(), (str(path), target)

before = json.loads((BEFORE / 'before-files.json').read_text())
changed = []
for filename, expected_hash in before.items():
    path = ROOT / filename
    assert path.is_file(), 'removed pre-existing file: ' + filename
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
        changed.append(filename)
assert set(changed) == {'PROJECT_STATUS.md', 'SecureExam-Implementation-Plan.md'}, changed
diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
assert diff.returncode == 0, diff.stdout + diff.stderr
report = {
    'status': 'PASS',
    'scope': 'documentation revision only',
    'command': 'python3 -B reports/cpjudge-scope-1/verify_docs.py',
    'exit_status': 0,
    'backlog_task_ids': len(rows),
    'selected_mvp_tasks': len(selected),
    'dependency_graph_acyclic': True,
    'mvp_dependency_closure_equals_h05_release_gate': True,
    'mvp_has_no_deferred_or_optional_prerequisites': True,
    'completed_task_rows_unchanged': completed,
    'deferred_task_rows': sorted(deferred),
    'component_deferrals': ['participant groups', 'general announcements', 'ratings', 'matchmaking', 'participant-format selector'],
    'new_feature_tasks_not_started': ['C15', 'C16', 'C17', 'E17'],
    'document_local_links_resolve': True,
    'git_diff_check_exit_status': diff.returncode,
    'preexisting_files_checked': len(before),
    'preexisting_files_changed': sorted(changed),
    'all_other_preexisting_files_byte_identical': True,
    'dependency_pins_and_previous_reports_unchanged': True,
    'application_tests_run': False,
    'dependency_installation_or_judging_run': False,
    'commit_or_push': False,
    'open_inputs': ['official IIITD logo asset', 'exact account/device-session binding semantics'],
    'documents_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in DOCS},
    'baseline_snapshot': str(BEFORE.relative_to(ROOT)),
}
OUT.write_text(json.dumps(report, indent=2) + '\n')
print('PASS: documentation links/dependencies, completed milestones and preservation; no application tests run.')
