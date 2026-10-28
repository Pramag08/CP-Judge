"""Conversion -> installed problem -> official DMOJ tests in an isolated container."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from compat.convert import convert, extract
from tools.make_fixtures import build
from tools.install_judge_tests import install


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--real', type=Path)
    p.add_argument('--judge-image', default='cp-judge-compat')
    p.add_argument('--judge', action='store_true')
    args = p.parse_args()
    if args.output.exists():
        p.error('output must be new')
    args.output.mkdir(parents=True)
    build(args.output / 'fixtures')
    problems = args.output / 'problems'
    problems.mkdir()
    report = {'conversion': {}, 'judging': 'NOT TESTED', 'reason': 'use --judge on an isolated Docker worker'}
    packages = list(sorted((args.output / 'fixtures').glob('*.zip')))
    if args.real:
        packages.append(args.real)
    for n, package in enumerate(packages):
        dest = args.output / f'converted-{n}'
        slug = convert(package, dest)
        shutil.copytree(dest / slug, problems / slug)
        if package == args.real:
            with tempfile.TemporaryDirectory() as temp:
                source = Path(temp)
                extract(package, source)
                # Only a declared main source is eligible; it is never executed on the host.
                from defusedxml import ElementTree as ET
                from compat.convert import required
                doc = ET.parse(source / 'problem.xml').getroot()
                main = doc.find('assets/solutions/solution[@tag="main"]/source')
                if main is None:
                    raise ValueError('real package has no main source for accepted test')
                install(problems / slug, slug, required(source, main.get('path')))
                # Preserve the declared source language standard for reference and probes.
                import re, yaml
                lang = re.search(r'g\+\+(11|14|17|20|23)$', main.get('type', ''))
                if not lang:
                    raise ValueError('unsupported reference source language')
                config_path = problems / slug / 'init.yml'
                conf = yaml.safe_load(config_path.read_text())
                for t in conf['tests']:
                    t['language'] = 'CPP' + lang.group(1)
                config_path.write_text(yaml.safe_dump(conf, sort_keys=False))
        else:
            install(problems / slug, slug)
        report['conversion'][slug] = 'PASS (real package)' if package == args.real else 'PASS (SYNTHETIC)'
    status = 0
    if args.judge:
        if not shutil.which('docker'):
            report.update(judging='NOT TESTED', reason='docker executable is missing')
            status = 2
        else:
            config = args.output / 'judge.yml'
            config.write_text('problem_storage_root:\n  - /problems\n')
            cmd = ['docker', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=ALL',
                   '--cap-add=SYS_PTRACE', '--security-opt=no-new-privileges', '--pids-limit=128',
                   '--memory=2g', '--cpus=2', '--tmpfs=/tmp:rw,exec,nosuid,size=1g,mode=1777',
                   '--mount', f'type=bind,src={problems.resolve()},dst=/problems,readonly',
                   '--mount', f'type=bind,src={config.resolve()},dst=/config.yml,readonly',
                   '--entrypoint=/compat-entry', args.judge_image, 'test', *report['conversion']]
            report['command'] = cmd
            with (args.output / 'judge.log').open('w') as log:
                try:
                    proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=600)
                    text = (args.output / 'judge.log').read_text()
                    # Official tester skips unavailable executors with exit 0: never call that PASS.
                    ok = proc.returncode == 0 and 'All tests passed.' in text and 'Skipped' not in text
                    report.update(judging='PASS' if ok else 'FAIL', reason='see judge.log')
                    status = 0 if ok else 1
                except (OSError, subprocess.TimeoutExpired) as e:
                    report.update(judging='FAIL', reason=str(e))
                    status = 1
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return status


if __name__ == '__main__':
    sys.exit(main())
