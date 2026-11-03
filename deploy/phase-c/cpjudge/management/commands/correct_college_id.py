from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cpjudge.identity import correct_id

class Command(BaseCommand):
    help='Audited college ID assignment/correction. Preserves username, password and history; revokes sessions.'
    def add_arguments(self, parser):
        parser.add_argument('user_id',type=int)
        parser.add_argument('college_id')
        parser.add_argument('--actor',required=True)
        parser.add_argument('--reason',required=True)
    def handle(self,*args,**o):
        actor=get_user_model().objects.get(username=o['actor'])
        correct_id(actor,o['user_id'],o['college_id'],o['reason'])
        self.stdout.write('College ID corrected and sessions revoked. Username, password and history preserved.')
