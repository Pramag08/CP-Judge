"""Allowlisted private conversion preview; never serve a raw report or package file."""
import json
import math
import re
import yaml

# Exact converter reasons only. Dynamic filenames, paths and framework errors
# must never cross this boundary. Corrections are author actions, not downgrades.
CORRECTIONS = {
    'only standard batch problems supported': 'Unsupported problem type. Export a standard batch problem; interactive tasks need a different judging integration.',
    'interactive problems unsupported': 'Interactive problems are unsupported. Provide a genuinely non-interactive batch version with fixed input/answer tests, or use a platform with interactor support.',
    'unknown judging policy': 'Unsupported judging policy. Use a standard batch export with only supported judging attributes; ask the organizer to review any required custom policy.',
    'missing judging, file I/O, or multiple runs unsupported': 'Missing judging metadata, file I/O, or multiple runs are unsupported. Declare one run using standard input/output in problem.xml and supply matching tests.',
    'exactly one testset required': 'Multiple or missing testsets are unsupported. Export exactly one complete testset.',
    'unknown testset policy': 'Unsupported testset policy. Export a single standard testset without custom policy attributes.',
    'unknown testset feature': 'Unsupported testset feature. Use declared time/memory limits, test count, input/answer patterns, tests and supported complete-group scoring; request support for other required semantics.',
    'limits must be positive': 'Invalid limits. Declare positive time in milliseconds and memory in bytes in problem.xml.',
    'invalid short-name': 'Invalid problem short-name. Use only ASCII letters, digits, underscore and hyphen.',
    'test-count mismatch or empty tests': 'Test count is empty or inconsistent. Export all test/answer pairs and make test-count match the tests list.',
    'group-level policy attributes unsupported': 'Unsupported group policy attributes. Export explicit complete-group scoring without custom group-container policies.',
    'invalid sample flag': 'Invalid sample flag. Mark each sample as true or false in problem.xml.',
    'unsupported per-test scoring or metadata': 'Per-test scoring or custom test metadata is unsupported. Use supported complete-group scoring or request support for the intended scoring; do not discard required scoring.',
    'only explicit complete-group scoring supported': 'Unsupported scoring policy. Only explicit complete-group scoring is supported. Export that policy only if it preserves the intended rules; otherwise request scoring support.',
    'unknown group feature': 'Unsupported scoring group feature. Use complete-group points and dependencies, or request support for the required feature.',
    'unknown group dependency feature': 'Unsupported group dependency metadata. Declare dependencies using group references only.',
    'group points must be positive integers (zero/fractional scoring unsupported)': 'Zero or fractional group points are unsupported. Use positive integer group points only if equivalent to the intended scoring; otherwise request scoring support.',
    'duplicate/empty groups or tests without a declared group': 'Invalid scoring groups. Give each group a unique name and at least one test, and assign every test to a declared group.',
    'test refers to undeclared group': 'A test references an undeclared group. Declare that group and its intended scoring in problem.xml.',
    'an explicit testlib checker source is required; no default substitution': 'Missing or unsupported checker. Export an explicit C++ testlib checker with source; no default checker is substituted.',
    'only C++ testlib checkers supported': 'Unsupported checker language. Supply an equivalent C++ testlib checker, or request support for the original checker language.',
    'checker source must declare a supported g++11/14/17/20/23 standard': 'Unsupported or missing checker compiler standard. Declare the actual required g++11, g++14, g++17, g++20 or g++23 standard. If another standard is required, request executor support; do not relabel or downgrade it.',
    'checker partial-points protocol or per-case scoring unsupported': 'Checker partial-points protocols are unsupported. Supply a pass/fail checker only if it preserves the intended scoring; otherwise request partial-points support.',
    'nested checker includes unsupported': 'Nested checker includes are unsupported. Export local checker headers with flat include names and update includes consistently.',
    'an HTML or PDF statement required': 'Missing supported statement file. Include an HTML or PDF statement in the export. Safe statement preview is a later check.',
    'problem.xml exceeds metadata budget': 'Problem metadata is too large. Reduce problem.xml to the required metadata and export again.',
    'test group dependencies contain a cycle': 'Cyclic scoring dependencies are unsupported. Correct the dependency graph so it is acyclic without changing the intended scoring rules.',
    'problem time limit must be a positive 32-bit integer in milliseconds': 'Invalid time limit. Declare a positive 32-bit integer time limit in milliseconds in problem.xml.',
    'problem memory limit must be a positive 32-bit integer in MiB': 'Invalid memory limit. Review the declared memory in bytes; the converter must represent its MiB intermediate as a positive 32-bit integer.',
    'referenced checker has no source file or inline content': 'The checker source is empty or missing. Export the complete C++ testlib checker source.',
    'DMOJ batch dependencies must refer to an earlier test group': 'Unsupported dependency order. Order scoring groups so every dependency refers to an earlier group, preserving the same dependency graph.',
}
# ArchiveRejected reasons are fixed strings in the strict extractor.
_ARCHIVE_GUIDANCE = {
    'paths': ('Unsafe archive path', 'Absolute, traversal or ambiguous archive path',
              'Archive path exceeds length/depth limit', 'Reserved archive path',
              'ZIP member name exceeds path limit', 'Truncated or ambiguous ZIP filename',
              'Ambiguous archive directory spelling', 'Duplicate or ambiguous archive path',
              'File/directory archive path conflict', 'Symlinks and special archive entries are forbidden'),
    'size': ('ZIP exceeds entry count limit', 'Actual ZIP entry count exceeds limit',
             'ZIP exceeds upload byte limit', 'ZIP exceeds expansion/ratio limit',
             'Actual extracted bytes exceed expansion limit'),
    'format': ('Invalid ZIP end record', 'Ambiguous ZIP end record or trailing data',
               'Multi-disk and ZIP64 packages are unsupported', 'ZIP central-directory bounds mismatch',
               'Invalid ZIP directory entry', 'ZIP directory entry exceeds bounds',
               'ZIP declared/actual entry count mismatch', 'Encrypted archive entries are unsupported',
               'Unsupported ZIP compression method', 'ZIP declared/actual member size mismatch',
               'Invalid or unsupported ZIP archive'),
}
for _category, _reasons in _ARCHIVE_GUIDANCE.items():
    for _reason in _reasons:
        CORRECTIONS[_reason] = _reason + '. ' + {
            'paths': 'Re-export regular files using unique, short relative paths without links, traversal or reserved names.',
            'size': 'Reduce package size or entry count and include only required files; ask the organizer to review configured limits.',
            'format': 'Re-export a valid, unencrypted, single-disk ZIP using stored or deflated compression without ZIP64.',
        }[_category]
GENERIC_ERROR = ('Package metadata could not be validated. Check well-formed problem.xml, '
                 'required test/answer files, checker standard and scoring. Export a corrected ZIP; '
                 'ask the organizer for details if the required feature is not supported.')


def rejection_message(exc):
    reason = str(exc)
    if reason in CORRECTIONS:
        return CORRECTIONS[reason]
    for prefix, message in (
        ('missing required package file:', 'A required package file is missing. Re-export all files referenced by problem.xml, including tests, answers, statement and checker headers.'),
        ('unsafe package path:', 'An unsafe package path is unsupported. Export relative paths without parent traversal, drive prefixes or backslashes.'),
        ('unsupported test path pattern:', 'Unsupported test filename pattern. Use one integer placeholder such as %03d in each input/answer path pattern and include every numbered pair.'),
    ):
        if reason.startswith(prefix):
            return message
    for pattern, message in GROUP_ERRORS.items():
        if re.fullmatch(pattern, reason, re.DOTALL):
            return message
    return GENERIC_ERROR


GROUP_ERRORS = {
    r'test group .* lists a dependency more than once': 'Duplicate scoring dependencies are unsupported. List each dependency once in problem.xml.',
    r'test group .* references unknown dependencies: .*': 'A scoring dependency references an undeclared group. Declare the intended dependency group and preserve its points and tests.',
    r'test group .* depends on itself': 'A scoring group depends on itself. Correct the dependency graph to be acyclic while preserving the intended scoring.',
    r'DMOJ checker source references missing local files: .*': 'The checker references missing local files. Include every required checker header in the export with flat include names.',
}


PUBLIC_REJECTIONS = frozenset(CORRECTIONS.values()) | frozenset(GROUP_ERRORS.values()) | {GENERIC_ERROR} | {
    rejection_message(ValueError(prefix)) for prefix in (
        'missing required package file:', 'unsafe package path:', 'unsupported test path pattern:')}


ISSUE_GUIDANCE = {
    'dmoj-samples-sidecar': 'Samples are retained as private sidecars. This strict adapter also keeps them as active tests.',
    'dmoj-inert-attachments': 'Attachments are preserved as inert files without website import semantics; safe asset handling is a later check.',
    'dmoj-multilingual-statement': 'Only one statement sidecar is written by the upstream writer; original statement assets remain private. Language preview is not verified.',
    'dmoj-validator': 'A validator is preserved without execution; validation of generated tests is not verified.',
    'dmoj-file-io': 'File I/O metadata needs review. This strict adapter rejects file I/O packages; do not treat this output as verified support.',
}


def preview(job):
    """Only current, manifest-owned successful output is eligible. No extraction."""
    if job.status != 'succeeded':
        return None
    from .conversion import attempt_path
    try:
        base = attempt_path(job.token)
        if json.loads((base/'owner.json').read_text()) != {
                'job_id': job.pk, 'attempt': job.attempt, 'token': job.token}:
            return None
        if job.findings.get('converted_directory') != 'attempts/'+job.token+'/output':
            return None
        slug = job.findings.get('slug', '')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', slug):
            return None
        output = base/'output'
        report = json.loads((output/'conversion-report.json').read_text())
        meta = json.loads((output/(slug+'.metadata.json')).read_text())
        config = yaml.safe_load((output/slug/'init.yml').read_text())
        if report['source_sha256'] != job.package_sha256:
            return None
        cases = config['test_cases']
        count = sum(len(c['batched']) if 'batched' in c else 1 for c in cases)
        if count != len(report['test_hashes']):
            return None
        if (config['time_limit'] != report['time_ms']/1000 or
                config['memory_limit'] != math.ceil(report['memory_bytes']/1024) or
                config['checker']['args']['lang'] != report['checker_executor']):
            return None
        groups = [{'number': i, 'tests': len(c['batched']), 'points': c.get('points'),
                   'dependencies': c.get('dependencies', [])}
                  for i,c in enumerate(cases, 1) if 'batched' in c]
        return {
            'name': meta.get('title'), 'code': meta.get('code'),
            'test_count': count, 'sample_count': len(report['samples']),
            'time_ms': report['time_ms'], 'seconds': config['time_limit'],
            'memory_bytes': report['memory_bytes'], 'kib': config['memory_limit'],
            'standard': report['checker_executor'], 'source_type': report.get('checker_source_type'),
            'groups': groups, 'issue_count': len(report.get('issues', [])),
            'checker': 'C++ testlib (bridged)',
            'warnings': [ISSUE_GUIDANCE.get(issue.get('code'),
                'An additional conversion issue was recorded. Ask the organizer to review the private diagnostic before later checks.')
                for issue in report.get('issues', [])],
        }
    except (OSError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError):
        return None


def public_error(job):
    """Old/unknown stored errors are never a raw-log display channel."""
    from .conversion import PUBLIC_ERRORS
    safe = PUBLIC_REJECTIONS | PUBLIC_ERRORS | {
        'The conversion queue is unavailable. Please retry.',
        'Import permission was revoked or the account is unavailable.',
        'Conversion was interrupted or did not start before its deadline. Please retry.',
        'Conversion failed. Review problem.xml, test files, checker standard and scoring; then retry.',
    }
    return job.error if job.error in safe else GENERIC_ERROR
