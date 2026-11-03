"""Local recovery requires container/operator access AND an active superuser actor."""
import json
import os
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from cpjudge.identity import provision, reset

class Command(BaseCommand):
    help = 'Provision/reset a college account; write temporary credential to a NEW private file.'
    def add_arguments(self, parser):
        parser.add_argument('action', choices=['provision','reset'])
        parser.add_argument('college_id')
        parser.add_argument('--actor', required=True)
        parser.add_argument('--credential-file', required=True)
        parser.add_argument('--first-name', default='')
        parser.add_argument('--last-name', default='')
        parser.add_argument('--email', default='')
        parser.add_argument('--author', action='store_true')
    def handle(self, *args, **options):
        actor = get_user_model().objects.get(username=options['actor'])
        from cpjudge.identity import require_admin
        require_admin(actor)
        path = Path(options['credential_file'])
        if not path.is_absolute():
            raise CommandError('Use an absolute private credential-file path.')
        # Reserve output first so an existing file never causes a half-reported reset.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with transaction.atomic():
                if options['action'] == 'reset':
                    raise CommandError('Use account_password_reset with verified requester, user PK and private reason file.')
                else:
                    user, password = provision(actor, options['college_id'], first_name=options['first_name'],
                        last_name=options['last_name'], email=options['email'], author=options['author'])
                payload = json.dumps({'username':user.username, 'password':password}).encode()
                with os.fdopen(os.dup(fd), 'wb') as output:
                    output.write(payload)
                    output.flush()
                    os.fsync(output.fileno())
        finally:
            os.close(fd)
        self.stdout.write('Credential saved privately; password change is optional.')
