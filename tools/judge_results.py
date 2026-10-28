"""Summarize pinned dmoj-cli output without private sources, data or checker messages."""
import collections
import re

ANSI = re.compile(r'\x1b\[[0-9;]*m')


def summarize(log, expectations, returncode):
    text = ANSI.sub('', log)
    records = {}
    current_problem = current = None
    for line in text.splitlines():
        match = re.search(r'Testing problem (\S+)\.\.\.', line)
        if match:
            current_problem = match[1]
            continue
        match = re.search(r'Running test (\S+)$', line.strip())
        if match and current_problem:
            current = records.setdefault(current_problem, {}).setdefault(match[1], {'cases': [], 'result': 'INCOMPLETE'})
            continue
        match = re.search(r'Test case\s+(\d+)\s+(AC|WA|RTE|TLE|MLE|OLE|IR|CE|IE|--)(?=\s|$)', line)
        if match and current is not None:
            current['cases'].append((int(match[1]), 'SC' if match[2] == '--' else match[2]))
        match = re.search(r'Result of test \S+: (Success|Failed)', line)
        if match and current is not None:
            current['result'] = match[1]
    issues = []
    if 'Skipped' in text:
        issues.append('SKIPPED_OR_MISSING_EXECUTOR')
    if 'Unexpected internal error' in text or 'InternalError' in text:
        issues.append('JUDGE_OR_CHECKER_ERROR')
    if 'Failed compiling submission' in text or 'Unexpected compile error' in text:
        issues.append('COMPILATION_ERROR')
    if 'failed with exception' in text or 'Traceback (most recent call last)' in text:
        issues.append('SETUP_OR_JUDGE_EXCEPTION')
    if returncode:
        issues.append('NONZERO_EXIT')
    summary = {}
    for problem, probes in expectations.items():
        summary[problem] = {}
        for label, expected in probes.items():
            record = records.get(problem, {}).get(label, {'cases': [], 'result': 'MISSING'})
            actual = record['cases']
            complete = [n for n, _ in actual] == list(range(1, len(expected) + 1))
            verdicts_match = [code for _, code in actual] == expected
            passed = record['result'] == 'Success' and complete and verdicts_match
            summary[problem][label] = {'status': 'PASS' if passed else 'FAIL', 'expected_cases': len(expected),
                                       'observed_cases': len(actual), 'verdict_counts': dict(collections.Counter(code for _, code in actual)),
                                       'complete': complete, 'expected_verdicts_match': verdicts_match}
            if not passed:
                issues.append(f'INCOMPLETE_OR_FAILED_PROBE:{problem}/{label}')
    if 'All tests passed.' not in text:
        issues.append('MISSING_COMPLETION_MARKER')
    return {'status': 'PASS' if not issues else 'FAIL', 'issues': issues, 'probes': summary}
