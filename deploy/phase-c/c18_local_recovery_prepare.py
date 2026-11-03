"""Prepare private reason-only operator recovery input; do not roll back live mode."""
import json,os,stat
from pathlib import Path
from django.contrib.auth import get_user_model
from cpjudge.email_identity import email_only
actor=get_user_model().objects.get(pk=1)
assert actor.is_active and actor.is_superuser and email_only()
folder=Path('/app/private-cpj-ops');assert not folder.is_symlink();folder.mkdir(mode=0o700,exist_ok=True);folder.chmod(0o700)
p=folder/'c18-local-recovery.json'
body={'reason':'Explicit local administrator recovery: temporarily restore transitional login, retain all canonical mappings/passwords/data, revoke sessions; guarded email-only re-cutover remains required.'}
if p.exists():assert not p.is_symlink() and json.loads(p.read_text())==body
else:
 with p.open('x') as f:p.chmod(0o600);json.dump(body,f)
assert p.stat().st_uid==os.getuid() and stat.S_IMODE(p.stat().st_mode)==0o600
print('Private reason-only local administrator recovery input prepared and permissions verified; live email-only mode remains enabled.')
