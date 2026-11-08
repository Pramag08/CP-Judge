import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from defusedxml import ElementTree as ET
import yaml

ROOT = Path(__file__).resolve().parents[1]


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


class Unsupported(ValueError):
    pass


def upstream():
    dep = json.loads((ROOT / 'dependencies.json').read_text())['converter']
    path = Path(os.environ.get('PCC_ROOT', ROOT / '.deps/converter')).resolve()
    commit = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != dep['commit']:
        raise Unsupported('converter commit differs from dependencies.json')
    if subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain', '--untracked-files=no']):
        raise Unsupported('converter checkout has tracked modifications')
    sys.path.insert(0, str(path / 'runner'))
    import package_adapters as writer
    import package_ir as ir
    return writer, ir


def safe_path(root, name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
        raise Unsupported(f'unsafe package path: {name!r}')
    return root.joinpath(*p.parts)


def extract(archive, target, limits=None):
    from compat.archive import ArchiveRejected, extract_zip
    try:
        return extract_zip(archive, target, limits)
    except ArchiveRejected as exc:
        raise Unsupported(str(exc)) from exc


def required(root, name):
    p = safe_path(root, name)
    if not p.is_file():
        raise Unsupported(f'missing required package file: {name}')
    return p


def pattern_path(root, pattern, index):
    if not re.fullmatch(r'[^%]*%0?[1-9]?d[^%]*', pattern):
        raise Unsupported(f'unsupported test path pattern: {pattern}')
    return required(root, pattern % index)


def read(root, ir):
    xml = required(root, 'problem.xml')
    if xml.stat().st_size > 4 * 1024**2:
        raise Unsupported('problem.xml exceeds metadata budget')
    doc = ET.parse(xml).getroot()
    if doc.tag != 'problem' or doc.get('type', 'standard') != 'standard':
        raise Unsupported('only standard batch problems supported')
    if doc.find('.//interactor') is not None:
        raise Unsupported('interactive problems unsupported')
    judging = doc.find('judging')
    if judging is not None and set(judging.attrib) - {'cpu-name', 'cpu-speed', 'input-file', 'output-file', 'run-count'}:
        raise Unsupported('unknown judging policy')
    if judging is None or judging.get('input-file') or judging.get('output-file') or judging.get('run-count', '1') != '1':
        raise Unsupported('missing judging, file I/O, or multiple runs unsupported')
    sets = judging.findall('testset')
    if len(sets) != 1:
        raise Unsupported('exactly one testset required')
    ts = sets[0]
    if set(ts.attrib) - {'name'}:
        raise Unsupported('unknown testset policy')
    allowed = {'time-limit', 'memory-limit', 'test-count', 'input-path-pattern', 'answer-path-pattern', 'tests', 'groups'}
    if any(n.tag not in allowed for n in ts):
        raise Unsupported('unknown testset feature')
    time_ms, memory_bytes = int(ts.findtext('time-limit')), int(ts.findtext('memory-limit'))
    if time_ms <= 0 or memory_bytes <= 0:
        raise Unsupported('limits must be positive')
    slug = doc.get('short-name', '')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', slug):
        raise Unsupported('invalid short-name')
    p = ir.Problem(id=slug, slug=slug, title=doc.find('names/name').get('value'),
                   time_ms=time_ms, memory_mb=math.ceil(memory_bytes / 1024**2))
    manifest = {'kind': 'real-or-user-supplied', 'time_ms': time_ms, 'memory_bytes': memory_bytes,
                'samples': [], 'test_hashes': [], 'not_executed': ['generators', 'validators', 'package scripts']}
    tests = ts.findall('tests/test')
    if len(tests) != int(ts.findtext('test-count')) or not tests:
        raise Unsupported('test-count mismatch or empty tests')
    groups = ts.findall('groups/group')
    if groups and ts.find('groups').attrib:
        raise Unsupported('group-level policy attributes unsupported')
    for i, t in enumerate(tests, 1):
        if t.get('sample', 'false') not in {'true', 'false'}:
            raise Unsupported('invalid sample flag')
        if 'points' in t.attrib:
            raise Unsupported('per-test points unsupported')
        # Polygon may annotate a test with a human-readable description. It has
        # no judging or scoring semantics; keep rejecting all other metadata.
        if set(t.attrib) - {'method', 'cmd', 'sample', 'group', 'description'} or list(t):
            raise Unsupported('unsupported per-test scoring or metadata')
        ip = pattern_path(root, ts.findtext('input-path-pattern'), i)
        op = pattern_path(root, ts.findtext('answer-path-pattern'), i)
        # Keep sample tests active: upstream otherwise excludes them from grading.
        p.cases.append(ir.TestCase(str(i), ip, op, group=t.get('group'), score=1 if not groups else None))
        manifest['test_hashes'].append({'input': hashlib.sha256(ip.read_bytes()).hexdigest(),
                                        'answer': hashlib.sha256(op.read_bytes()).hexdigest()})
        if t.get('sample') == 'true':
            manifest['samples'].append(i)
    for g in groups:
        if set(g.attrib) - {'name', 'points', 'points-policy'} or g.get('points-policy') != 'complete-group':
            raise Unsupported('only explicit complete-group scoring supported')
        if any(c.tag != 'dependencies' for c in g):
            raise Unsupported('unknown group feature')
        if any(c.tag != 'dependency' or set(c.attrib) != {'group'} for c in g.findall('dependencies/*')):
            raise Unsupported('unknown group dependency feature')
        score = float(g.get('points', 'nan'))
        if not math.isfinite(score) or score <= 0 or not score.is_integer():
            raise Unsupported('group points must be positive integers (zero/fractional scoring unsupported)')
        p.groups.append(ir.TestGroup(g.get('name'), tuple(c.name for c in p.cases if c.group == g.get('name')),
                                     score, tuple(d.get('group') for d in g.findall('dependencies/dependency'))))
    if groups and (len({g.name for g in p.groups}) != len(groups) or
                   any(not g.cases for g in p.groups) or any(c.group not in {g.name for g in p.groups} for c in p.cases)):
        raise Unsupported('duplicate/empty groups or tests without a declared group')
    if not groups and any(c.group is not None for c in p.cases):
        raise Unsupported('test refers to undeclared group')
    checker = doc.find('assets/checker')
    if checker is None or checker.get('type') != 'testlib' or checker.find('source') is None:
        raise Unsupported('an explicit testlib checker source is required; no default substitution')
    src = required(root, checker.find('source').get('path'))
    if src.suffix != '.cpp':
        raise Unsupported('only C++ testlib checkers supported')
    language = checker.find('source').get('type', '')
    match = re.search(r'g\+\+(11|14|17|20|23)$', language)
    if not match:
        raise Unsupported('checker source must declare a supported g++11/14/17/20/23 standard')
    manifest['checker_executor'] = 'CPP' + match.group(1)
    manifest['checker_source_type'] = language
    manifest['compiler_note'] = 'Language standard preserved; exact Polygon compiler version and platform are not reproduced.'
    text = src.read_text()
    if re.search(r'quitp|_points|_partially|POINTS_EXIT_CODE', text):
        raise Unsupported('checker partial-points protocol or per-case scoring unsupported')
    aux = {}
    pending = [src]
    while pending:
        source = pending.pop()
        for name in re.findall(r'^\s*#\s*include\s*"([^"\n]+)"', source.read_text(), re.M):
            # DMOJ helper compilation flattens source names; reject nested headers.
            if PurePosixPath(name).name != name:
                raise Unsupported('nested checker includes unsupported')
            dep = required(source.parent, name)
            if name not in aux:
                aux[name] = dep
                pending.append(dep)
    p.checker = ir.Program('checker', language='C++', mode='testlib', path=src, auxiliary_files=aux)
    # Every statement format and supporting asset is preserved byte-for-byte as inert payload.
    for folder in ['statements', 'statement-sections']:
        for f in (root / folder).rglob('*'):
            if f.is_file():
                p.attachments[f.relative_to(root).as_posix()] = f
    for s in doc.findall('statements/statement'):
        path = required(root, s.get('path'))
        fmt = {'text/html': 'html', 'application/pdf': 'pdf'}.get(s.get('type'))
        if fmt:
            p.statements.append(ir.Statement(s.get('language'), fmt, path=path))
    if not p.statements:
        raise Unsupported('an HTML or PDF statement required')
    return p, manifest


def convert(archive, output):
    writer, ir = upstream()
    output = Path(output)
    if output.exists():
        raise Unsupported('output must not exist (prevent stale installation or overwrite)')
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / 'source'
        extract(archive, root)
        p, manifest = read(root, ir)
        bundle = ir.ProblemBundle('polygon', [p])
        bundle.validate_integrity()
        writer._validate_dmoj_target(bundle, {})
        bundle.ensure_convertible('warn')
        staged = Path(temp) / 'output'
        staged.mkdir()
        writer.write_dmoj(bundle, staged, {})
        install = staged / p.slug
        extract(staged / f'{p.slug}.zip', install)
        conf = yaml.safe_load((install / 'init.yml').read_text())
        conf['checker']['args']['lang'] = manifest['checker_executor']
        # DMOJ Submission uses seconds and KiB, not Polygon milliseconds/bytes.
        conf.update(time_limit=p.time_ms / 1000, memory_limit=math.ceil(manifest['memory_bytes'] / 1024),
                    short_circuit=False)
        for i in manifest['samples']:
            dest = install / 'sidecar/samples'
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p.cases[i-1].input_path, dest / f'{i}.in')
            shutil.copyfile(p.cases[i-1].output_path, dest / f'{i}.out')
        (install / 'init.yml').write_text(yaml.safe_dump(conf, sort_keys=False))
        # Replace the upstream ZIP too so it cannot install the uncorrected config.
        with zipfile.ZipFile(staged / f'{p.slug}.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            for f in sorted(install.rglob('*')):
                if f.is_file():
                    z.write(f, f.relative_to(install))
        manifest['issues'] = [vars(i) for i in bundle.issues]
        manifest['status'] = 'PASS: conversion only; judging NOT TESTED'
        manifest['source_sha256'] = file_sha256(archive)
        manifest['dependencies'] = json.loads((ROOT / 'dependencies.json').read_text())
        (staged / 'conversion-report.json').write_text(json.dumps(manifest, indent=2) + '\n')
        shutil.copytree(staged, output)
    return p.slug


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        print(convert(args.package, args.output))
    except (ValueError, OSError, ET.ParseError) as e:
        parser.exit(1, f'REJECTED: {e}\n')


if __name__ == '__main__':
    main()
