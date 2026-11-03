"""Read-only A02 metadata/export audit; never compile or run imported code."""
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

from defusedxml import ElementTree as ET
import yaml

root = Path('build/a02-converter-1/pipeline')
assert __debug__, 'assertions must be enabled'
old = json.loads(Path('reports/synthetic-preservation.json').read_text())
results = {}
for n, slug in enumerate(('groups', 'multiple', 'tokens', 'gaming-grid')):
    source = Path('local-packages/gaming-grid.zip') if slug == 'gaming-grid' else root/'fixtures'/f'{slug}.zip'
    if not source.exists():
        results[slug] = {'status':'NOT TESTED', 'reason':'source package absent'}
        continue
    converted = root/f'converted-{n}'
    installed = converted/slug
    conf = yaml.safe_load((installed/'init.yml').read_text())
    probe_conf = yaml.safe_load((root/'problems'/slug/'init.yml').read_text())
    with zipfile.ZipFile(source) as package:
        xml = ET.fromstring(package.read('problem.xml'))
        ts = xml.find('judging/testset')
        source_tests = ts.findall('tests/test')
        language = xml.find('assets/checker/source').get('type')
        standard = 'CPP' + re.search(r'g\+\+(11|14|17|20|23)$', language).group(1)
        assert conf['checker']['name'] == 'bridged'
        assert conf['checker']['args']['type'] == 'testlib'
        assert conf['checker']['args']['lang'] == standard
        assert probe_conf['checker'] == conf['checker']
        seconds = int(ts.findtext('time-limit'))/1000
        kib = (int(ts.findtext('memory-limit'))+1023)//1024
        assert conf['time_limit'] == probe_conf['time_limit'] == seconds
        assert conf['memory_limit'] == probe_conf['memory_limit'] == kib
        assert conf['short_circuit'] is False
        groups = ts.findall('groups/group')
        point_values, dependencies = [], []
        if groups:
            assert len(conf['test_cases']) == len(groups)
            positions = {g.get('name'):i for i,g in enumerate(groups,1)}
            for group, entry in zip(groups, conf['test_cases']):
                assert group.get('points-policy') == 'complete-group'
                points = float(group.get('points'))
                assert math.isfinite(points) and points > 0 and points.is_integer()
                expected = [{'in':f'{i}.in','out':f'{i}.out'} for i,t in enumerate(source_tests,1) if t.get('group')==group.get('name')]
                assert entry['batched'] == expected
                assert entry['points'] == points
                deps = [positions[d.get('group')] for d in group.findall('dependencies/dependency')]
                assert entry.get('dependencies',[]) == deps
                point_values.append(entry['points'])
                dependencies.append(deps)
        else:
            assert [(entry['in'],entry['out']) for entry in conf['test_cases']] == [(f'{i}.in',f'{i}.out') for i in range(1,len(source_tests)+1)]
            assert all(entry['points']==1 for entry in conf['test_cases'])
        if slug == 'gaming-grid':
            main = xml.find('assets/solutions/solution[@tag="main"]/source')
            probe_standard = 'CPP' + re.search(r'g\+\+(11|14|17|20|23)$', main.get('type')).group(1)
        else:
            probe_standard = 'CPP20'
        for probe in probe_conf['tests']:
            assert probe['language']==probe_standard
            assert probe['time']==seconds and probe['memory']==kib
    # Every exported byte, including corrected init.yml and data.zip, must match
    # its extracted conversion. This copy does not contain installed probe code.
    members = {p.relative_to(installed).as_posix():p for p in installed.rglob('*') if p.is_file()}
    with zipfile.ZipFile(converted/f'{slug}.zip') as export:
        assert len(export.namelist())==len(set(export.namelist()))
        assert set(export.namelist())==set(members)
        for name, path in members.items():
            with export.open(name) as zipped, path.open('rb') as extracted:
                assert hashlib.file_digest(zipped,'sha256').digest()==hashlib.file_digest(extracted,'sha256').digest()
    manifest = json.loads((converted/'conversion-report.json').read_text())
    assert manifest['status']=='PASS: conversion only; judging NOT TESTED'
    assert manifest['not_executed']==['generators','validators','package scripts']
    with source.open('rb') as data:
        source_hash = hashlib.file_digest(data,'sha256').hexdigest()
    historical_match = None
    if slug in old:
        historical_match = source_hash==old[slug]['source_sha256']
        assert historical_match, 'synthetic fixture differs from historical preservation evidence'
    results[slug] = {
        'status':'PASS', 'judging':'NOT TESTED',
        'checker_standard':standard, 'probe_standard':probe_standard,
        'time_seconds':seconds, 'memory_KiB':kib, 'active_cases':len(source_tests),
        'case_order_and_membership':'PASS', 'checker_type':'bridged/testlib',
        'exported_files_verified':len(members), 'exported_zip_matches_installed_bytes':'PASS',
        'group_points':point_values, 'group_dependencies':dependencies,
        'scoring':'complete-group' if groups else 'one point per case',
        'synthetic_matches_previous_fixture_hash':historical_match,
        'package_code_execution':'NOT RUN'}
print(json.dumps(results,indent=2))
