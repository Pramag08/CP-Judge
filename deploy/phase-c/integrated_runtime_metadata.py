import json
from pathlib import Path
from cpjudge.models import ContestVersionAdmission
p=Path('/tmp/integrated-fixture.json');data=json.loads(p.read_text());a=ContestVersionAdmission.objects.get(pk=data['admission_id'])
data['runtime_id']=a.runtime_id;p.write_text(json.dumps(data));p.chmod(0o600)
print('Fixture runtime resolved from the existing native executor key; no language or version changed.')
