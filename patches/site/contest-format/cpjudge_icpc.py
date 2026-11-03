"""CPJudge fixed individual preset; native DMOJ storage, hooks and display.

Extends DMOJ's AGPL ICPC format without changing other registered formats.
Rules: docs/contracts/contest-rules.md and contest-native-mapping.md.
"""
from collections import defaultdict
from math import floor
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy
from judge.contest_format.icpc import ICPCContestFormat
from judge.contest_format.registry import register_contest_format

FAILURES = frozenset(('WA', 'TLE', 'MLE', 'RTE'))

def full_ac(status, result, points, total):
    return status == 'D' and result == 'AC' and total > 0 and points == total


def score_attempts(start, attempts):
    """Read authoritative rows in receipt/ID order; floor each solved problem."""
    grouped = defaultdict(list)
    for attempt in sorted(attempts, key=lambda row: (row['date'], row['id'])):
        grouped[attempt['problem_id']].append(attempt)
    solved = penalty = 0
    data = {}
    for problem_id, rows in grouped.items():
        failures = 0
        elapsed = points = 0
        for row in rows:
            if full_ac(row['status'], row['result'], row['case_points'], row['case_total']):
                elapsed = floor((row['date'] - start).total_seconds())
                points = 1
                solved += 1
                penalty += elapsed + 1200 * failures
                break
            if row['status'] == 'D' and row['result'] in FAILURES:
                failures += 1
        data[str(problem_id)] = {'time': elapsed, 'points': points, 'penalty': failures}
    return solved, penalty, data


@register_contest_format('cpjudge_icpc_v1')
class CPJudgeICPCFormat(ICPCContestFormat):
    name = gettext_lazy('CPJudge Individual ICPC (20-minute penalty)')

    @classmethod
    def validate(cls, config):
        if config is None or config == {}:
            return
        if not isinstance(config, dict) or set(config) != {'penalty'} or type(config['penalty']) is not int or config['penalty'] != 20:
            raise ValidationError('CPJudge requires the fixed 20-minute penalty.')

    def __init__(self, contest, config):
        self.validate(config)
        super().__init__(contest, {'penalty': 20})

    def update_participation(self, participation):
        from judge.models import ContestParticipation
        if self.contest.time_limit is not None or self.contest.run_pretests_only:
            raise ValidationError('CPJudge requires the common contest clock and full tests.')
        if self.contest.contest_problems.exclude(points=1, partial=False).exists():
            raise ValidationError('CPJudge contest problems require one full-AC solved point.')
        with transaction.atomic():
            ContestParticipation.objects.select_for_update().get(pk=participation.pk)
            attempts = participation.submissions.values(
                'problem_id', 'submission__id', 'submission__date', 'submission__status',
                'submission__result', 'submission__case_points', 'submission__case_total',
            )
            rows = [dict(problem_id=row['problem_id'], **{key.removeprefix('submission__'): value
                    for key, value in row.items() if key.startswith('submission__')}) for row in attempts]
            score, penalty, data = score_attempts(self.contest.start_time, rows)
            participation.score = score
            participation.cumtime = penalty
            participation.tiebreaker = 0
            participation.format_data = data
            participation.save(update_fields=['score', 'cumtime', 'tiebreaker', 'format_data'])

    def get_short_form_display(self):
        yield 'Each full Accepted result solves one problem. Partial case points do not solve it.'
        yield 'Penalty is whole seconds from the common start plus 20 minutes per prior WA, TLE, MLE or runtime error.'
        yield 'Compilation errors add no penalty. Unsolved problems and attempts after the first AC add no penalty.'
        yield 'Rank by solved count, then lower penalty. Equal totals share a rank; tied rows use entry ID.'
