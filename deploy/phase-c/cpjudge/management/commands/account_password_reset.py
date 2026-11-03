"""Privileged outside-app verified recovery, with private credential output."""
import json,os
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand,CommandError
from django.core.exceptions import ValidationError
from django.db import transaction
from cpjudge.identity import require_admin,reset_account

class Command(BaseCommand):
    help='Audited organizer reset after outside-app verification; no email/token delivery.'
    def add_arguments(self,p):
        p.add_argument('--actor-id',type=int,required=True)
        p.add_argument('--private-file',required=True)
        p.add_argument('--output-file',required=True)
    def handle(self,*args,**o):
        actor=get_user_model().objects.get(pk=o['actor_id']);require_admin(actor)
        source=Path(o['private_file']);target=Path(o['output_file'])
        if not source.is_absolute() or source.is_symlink() or source.stat().st_mode & 0o077 or source.stat().st_uid!=os.getuid():
            raise CommandError('Use an operator-owned0600 private input file.')
        if not target.is_absolute() or target.is_symlink():raise CommandError('Use a NEW absolute private output file.')
        data=json.loads(source.read_text())
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with transaction.atomic():
                try:user,password=reset_account(actor,data['user_id'],reason=data['reason'],requester_verified=data['requester_verified'])
                except ValidationError:raise CommandError('Reset rejected: requester verification and audit reason are required, and rate limits apply.') from None
                with os.fdopen(os.dup(fd),'w') as f:
                    json.dump({'user_id':user.pk,'username':user.username,'email':user.email,'password':password},f);f.flush();os.fsync(f.fileno())
        finally:os.close(fd)
        self.stdout.write('Verified organizer reset recorded; credential saved privately and previous sessions revoked. Password change is optional.')
