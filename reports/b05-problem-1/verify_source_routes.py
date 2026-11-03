"""Confirm corrected XML reference XPath adds no untested HTTP targets."""
import json
from pathlib import Path
import zipfile
from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
with zipfile.ZipFile(ROOT / 'local-packages/gaming-grid.zip') as archive:
    xml = ET.fromstring(archive.read('problem.xml'))
    names = {name for name in archive.namelist() if name.startswith(('solutions/', 'checkers/')) and name.endswith(('.cpp', '.h'))}
    names.update(e.get('path') for e in xml.findall('assets/checker/source') + xml.findall('solutions/solution/source') if e.get('path'))
    names.add(str(Path(xml.find('assets/checker/source').get('path')).parent / 'testlib.h'))
    corrected = set(names)
    references = [e.get('path') for e in xml.findall('assets/solutions/solution/source') if e.get('path')]
    assert references, 'Reference metadata must actually be found'
    corrected.update(references)
    assert corrected == names, 'New targets require new HTTP privacy verification'
result = {'status': 'PASS', 'corrected_xml_xpath_targets_equal_tested_targets': True,
          'original_source_paths': len(corrected), 'reference_paths_found': len(references),
          'command': '.venv/bin/python -B reports/b05-problem-1/verify_source_routes.py', 'exit_status': 0}
(Path(__file__).resolve().parent / 'source-route-coverage.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS: corrected XML reference paths equal the already-tested HTTP source target set.')
