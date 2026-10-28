"""Independently verify source bytes and installed judge configuration."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import yaml
from defusedxml import ElementTree as ET


def verify(package, conversion):
    package, conversion = Path(package), Path(conversion)
    with zipfile.ZipFile(package) as src:
        xml = ET.fromstring(src.read('problem.xml'))
        slug = xml.get('short-name')
        installed = conversion / slug
        conf = yaml.safe_load((installed / 'init.yml').read_text())
        ts = xml.find('judging/testset')
        tests = ts.findall('tests/test')
        with zipfile.ZipFile(installed / 'data.zip') as data:
            for i, test in enumerate(tests, 1):
                for pattern, suffix in [('input-path-pattern', 'in'), ('answer-path-pattern', 'out')]:
                    assert src.read(ts.findtext(pattern) % i) == data.read(f'{i}.{suffix}'), (i, suffix)
                if test.get('sample') == 'true':
                    assert src.read(ts.findtext('input-path-pattern') % i) == (installed / f'sidecar/samples/{i}.in').read_bytes()
                    assert src.read(ts.findtext('answer-path-pattern') % i) == (installed / f'sidecar/samples/{i}.out').read_bytes()
        statement_files = [n for n in src.namelist() if n.startswith(('statements/', 'statement-sections/')) and not n.endswith('/')]
        for n in statement_files:
            assert src.read(n) == (installed / 'attachments' / n).read_bytes(), n
        checker = xml.find('assets/checker/source').get('path')
        assert src.read(checker) == (installed / 'checker.cpp').read_bytes()
        for header in conf['checker']['args']['files']:
            if header != 'checker.cpp':
                assert src.read(str(Path(checker).parent / header)) == (installed / header).read_bytes()
        assert conf['time_limit'] == int(ts.findtext('time-limit')) / 1000
        assert conf['memory_limit'] == (int(ts.findtext('memory-limit')) + 1023) // 1024
        groups = ts.findall('groups/group')
        if groups:
            entries = conf['test_cases']
            assert [c['points'] for c in entries] == [float(g.get('points')) for g in groups]
            positions = {g.get('name'): i for i, g in enumerate(groups, 1)}
            for entry, group in zip(entries, groups):
                assert entry.get('dependencies', []) == [positions[d.get('group')] for d in group.findall('dependencies/dependency')]
        active = sum(len(c['batched']) if 'batched' in c else 1 for c in conf['test_cases'])
        assert active == len(tests)
    return {'status': 'PASS', 'tests_verified': len(tests), 'statement_assets_verified': len(statement_files),
            'sample_tests_verified': sum(t.get('sample') == 'true' for t in tests), 'checker_bytes': 'PASS',
            'limits_and_groups': 'PASS (configuration only)', 'judging': 'NOT TESTED',
            'source_sha256': hashlib.sha256(package.read_bytes()).hexdigest()}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('package')
    p.add_argument('conversion')
    a = p.parse_args()
    print(json.dumps(verify(a.package, a.conversion), indent=2))
