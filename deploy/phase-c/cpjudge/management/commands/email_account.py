"""Operator-only identity workflow; all private input/output uses protected files."""
import json,os
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction,IntegrityError
from django.core.exceptions import ValidationError
from cpjudge.identity import require_admin
from cpjudge.email_identity import inventory,stage_keys,set_mode,correct_email,provision_email

class Command(BaseCommand):
    help='Private email inventory/staging/provision/correction/cutover/rollback; no email delivery.'
    def add_arguments(self,p):
        p.add_argument('action',choices=['inventory','stage','provision','correct','cutover','rollback'])
        p.add_argument('--actor-id',type=int,required=True)
        p.add_argument('--private-file',required=True)
        p.add_argument('--output-file')
    def handle(self,*args,**o):
        actor=get_user_model().objects.get(pk=o['actor_id']);require_admin(actor)
        path=Path(o['private_file'])
        if not path.is_absolute() or path.is_symlink():raise CommandError('Use an absolute protected private file.')
        if o['action']=='inventory':
            mapping,issues=inventory()
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as f:json.dump({'mapping':mapping,'issues':issues},f)
            self.stdout.write('Private inventory saved. No addresses printed.');return
        if path.stat().st_mode & 0o077 or path.stat().st_uid!=os.getuid():raise CommandError('Input must be owned by the operator UID with mode0600.')
        data=json.loads(path.read_text())
        try:
            with transaction.atomic():
                action=o['action']
                if action=='stage':stage_keys(actor)
                elif action in ('cutover','rollback'):set_mode(actor,action=='cutover',data['reason'])
                elif action=='correct':correct_email(actor,data['user_id'],data['email'],data['reason'])
                elif action=='provision':
                    target=Path(o['output_file'] or '')
                    if not target.is_absolute() or target.is_symlink():raise CommandError('Use a NEW absolute private credential output file.')
                    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                    try:
                        user,password=provision_email(actor,data['email'],first_name=data.get('first_name',''),last_name=data.get('last_name',''),author=data.get('author',False))
                        with os.fdopen(os.dup(fd),'w') as f:
                            json.dump({'user_id':user.pk,'username':user.username,'email':user.email,'password':password},f);f.flush();os.fsync(f.fileno())
                    finally:os.close(fd)
        except (IntegrityError,ValidationError):raise CommandError('Identity operation rejected. Inspect the private inventory; no identity was reassigned.') from None
        self.stdout.write('Authorized identity operation completed; private data was not printed.')
