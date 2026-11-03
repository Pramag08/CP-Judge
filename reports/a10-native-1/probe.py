"""Narrow native-method checks; no Django, database, bridge or judging is run."""
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'build/a09-site-1/site'
OUT = Path(__file__).resolve().parent
PIN = '604d60cfd764bc708b04ffd75b715a5398b91f8b'
FILES = ['judge/models/contest.py', 'judge/contest_format/icpc.py',
         'judge/models/submission.py', 'judge/views/contests.py',
         'judge/views/problem.py', 'judge/models/profile.py',
         'judge/middleware.py', 'judge/utils/ranker.py',
         'judge/contest_format/registry.py', 'judge/contest_format/__init__.py',
         'judge/judgeapi.py', 'judge/bridge/judge_handler.py']


def git(*args):
    result = subprocess.run(['git', '-C', str(SITE), *args], capture_output=True, check=True)
    return result.stdout


assert git('rev-parse', 'HEAD').decode().strip() == PIN
assert git('status', '--porcelain') == b''
hashes = {}
for filename in FILES:
    data = (SITE / filename).read_bytes()
    assert data == git('show', f'{PIN}:{filename}')
    hashes[filename] = hashlib.sha256(data).hexdigest()


def method(filename, classname, name, env=None):
    tree = ast.parse((SITE / filename).read_text())
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == classname)
    node = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)
    node.decorator_list = []
    namespace = {} if env is None else env.copy()
    exec(compile(ast.Module(body=[node], type_ignores=[]), filename, 'exec'), namespace)
    return namespace[name]


start = datetime(2026, 10, 28, 10, tzinfo=timezone.utc)
end = start + timedelta(hours=2)
contest = NS(start_time=start, end_time=end, time_limit=None, points_precision=0)
participation = NS(contest=contest, live=True, spectate=False, virtual=0,
                   real_start=start + timedelta(minutes=40), _now=start + timedelta(minutes=40))
native_start = method(FILES[0], 'ContestParticipation', 'start')
native_end = method(FILES[0], 'ContestParticipation', 'end_time')
native_ended = method(FILES[0], 'ContestParticipation', 'ended')
participation.start = native_start(participation)
participation.end_time = native_end(participation)
assert participation.start == start
assert participation.end_time == end
assert (participation.end_time - participation._now).total_seconds() == 4800
participation._now = end
assert native_ended(participation) is False
participation._now = end + timedelta(microseconds=1)
assert native_ended(participation) is True


class Query:
    def __init__(self, rows):
        self.rows = rows

    def exclude(self, **kw):
        if 'submission__result__isnull' in kw:
            return Query([r for r in self.rows if r.result is not None])
        return Query([r for r in self.rows if r.result not in kw['submission__result__in']])

    def filter(self, **kw):
        if 'problem_id' in kw:
            return Query([r for r in self.rows if r.problem_id == kw['problem_id']])
        return Query([r for r in self.rows if r.date <= kw['submission__date__lte']])

    def count(self):
        return len(self.rows)


class Cursor:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, args):
        assert 'MAX(cs.points)' in sql
        assert args == (1, 1)

    def fetchall(self):
        return self.rows


def native_score(aggregate_rows, attempts):
    # SQL aggregate output is an explicit fixture, not an executed SQL query.
    connection = NS(cursor=lambda: Cursor(aggregate_rows))
    update = method(FILES[1], 'ICPCContestFormat', 'update_participation',
                    {'connection': connection, 'from_database_time': lambda value: value})
    p = NS(id=1, start=start, submissions=Query(attempts), save=lambda: None)
    update(NS(config={'penalty': 20}, contest=contest), p)
    return {'score': p.score, 'cumtime_assigned': p.cumtime,
            'tiebreaker': p.tiebreaker, 'format_data': p.format_data}


def attempt(result, seconds, problem=1):
    return NS(result=result, date=start + timedelta(seconds=seconds), problem_id=problem)


observations = {}
observations['two_failures_ac_35m'] = native_score(
    [(1, start + timedelta(minutes=35), 1)],
    [attempt('WA', 100), attempt('TLE', 200), attempt('AC', 2100)])
assert observations['two_failures_ac_35m']['cumtime_assigned'] == 4500
observations['late_entry_ac_50m'] = native_score(
    [(1, start + timedelta(minutes=50), 1)], [attempt('AC', 3000)])
assert observations['late_entry_ac_50m']['cumtime_assigned'] == 3000
observations['ole_ir_sc_ab_before_ac'] = native_score(
    [(1, start + timedelta(minutes=35), 1)],
    [attempt(code, 100 + i) for i, code in enumerate(('OLE', 'IR', 'SC', 'AB'))] + [attempt('AC', 2100)])
assert observations['ole_ir_sc_ab_before_ac']['cumtime_assigned'] == 6900
observations['same_timestamp_two_ac'] = native_score(
    [(1, start + timedelta(minutes=35), 1)], [attempt('AC', 2100), attempt('AC', 2100)])
assert observations['same_timestamp_two_ac']['cumtime_assigned'] == 3300
observations['fractional_solve_sum'] = native_score(
    [(1, start + timedelta(seconds=60.6), 1), (1, start + timedelta(seconds=120.6), 2)],
    [attempt('AC', 60.6), attempt('AC', 120.6, 2)])
assert abs(observations['fractional_solve_sum']['cumtime_assigned'] - 181.2) < 0.00001
observations['unsolved_has_no_total_penalty'] = native_score(
    [(0, start + timedelta(seconds=100), 1)], [attempt('WA', 100)])
assert observations['unsolved_has_no_total_penalty']['cumtime_assigned'] == 0

update_contest = method(FILES[2], 'Submission', 'update_contest')
for label, case_points, case_total, result in [('rounded_partial', 9996, 10000, 'AC'),
                                               ('full_points_non_ac', 10, 10, 'RTE')]:
    cs = NS(problem=NS(points=1, partial=False), save=lambda: None,
            participation=NS(recompute_results=lambda: None))
    update_contest(NS(contest=cs, case_points=case_points, case_total=case_total, result=result))
    assert cs.points == 1
    observations[label] = {'native_contest_points': cs.points, 'case_points': case_points,
                           'case_total': case_total, 'result': result,
                           'contract_contest_points': 0}

rank_ns = {}
exec(compile((SITE / 'judge/utils/ranker.py').read_text(), 'judge/utils/ranker.py', 'exec'), rank_ns)
ranker = rank_ns['ranker']
users = [NS(name='a', points=2, cumtime=3600, tiebreaker=1800),
         NS(name='b', points=2, cumtime=3600, tiebreaker=2400),
         NS(name='c', points=1, cumtime=100, tiebreaker=100)]
stock_ranks = [rank for rank, _ in ranker(users, key=lambda row: (row.points, row.cumtime, row.tiebreaker))]
contract_ranks = [rank for rank, _ in ranker(users, key=lambda row: (row.points, row.cumtime))]
assert stock_ranks == [1, 2, 3]
assert contract_ranks == [1, 1, 3]
observations['ties'] = {'stock_ranks': stock_ranks, 'contract_ranks_with_native_ranker': contract_ranks}

output = {'status': 'PASS', 'scope': 'native method branch checks with explicit aggregate/query fixtures',
          'source_commit': PIN, 'source_clean_and_bytes_match_git': True,
          'source_sha256': hashes, 'late_entry': {'join_minutes': 40, 'start': start.isoformat(),
          'end': end.isoformat(), 'remaining_seconds_at_join': 4800,
          'native_ended_at_exact_deadline': False}, 'observations': observations,
          'not_executed': ['SQL aggregation', 'Django ORM/database persistence', 'HTTP deadline races',
                           'CPJudge scorer implementation', 'bridge/worker compatibility', 'actual judging'],
          'command': 'python3 -B reports/a10-native-1/probe.py', 'exit_status': 0}
(OUT / 'evidence.json').write_text(json.dumps(output, indent=2) + '\n')
print('PASS: native clock, scoring branch differences and ranker checked; no database or judging run.')
