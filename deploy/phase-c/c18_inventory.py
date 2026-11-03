import json,os
from pathlib import Path
from django.contrib.auth import get_user_model
from cpjudge.email_identity import inventory,stage_keys,set_mode
from django.core.exceptions import ValidationError
actor=get_user_model().objects.filter(is_active=True,is_superuser=True).order_by('pk').first();assert actor
mapping,issues=inventory()
p=Path('/tmp/c18-private-inventory.json');assert not p.exists()
p.write_text(json.dumps({'mapping':mapping,'issues':issues}));p.chmod(0o600)
result=stage_keys(actor)
try:set_mode(actor,True,'C18 guarded cutover acceptance')
except ValidationError:blocked=True
else:raise AssertionError('Unresolved identities must prevent cutover')
assert result=={'mapped':5,'unresolved':4}
Path('/tmp/c18-inventory-summary.json').write_text(json.dumps({'status':'BLOCKED','mapped':5,'missing':4,'invalid':0,'conflict_groups':0,'email_only_enabled':False,'organizer_verified_corrections_required':True}))
print('Five unique canonical keys staged; four missing emails block email-only cutover. Private inventory retained, no addresses printed.')
