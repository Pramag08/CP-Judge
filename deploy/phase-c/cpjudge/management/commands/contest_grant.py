from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from judge.models import Contest
from cpjudge.policy import grant_scope
class Command(BaseCommand):
    help='Create/revoke an explicit audited contest capability; never a global permission.'
    def add_arguments(self,p):
        p.add_argument('contest');p.add_argument('username');p.add_argument('capability')
        p.add_argument('--actor',required=True);p.add_argument('--revoke',action='store_true')
    def handle(self,*args,**o):
        if not o['revoke'] and o['capability'] not in ('roster.read','roster.export'):
            self.stdout.write('Content-management grants permanently make this entrant unranked in this contest.')
        U=get_user_model()
        grant_scope(U.objects.get(username=o['actor']),U.objects.get(username=o['username']),
                    Contest.objects.get(key=o['contest']),o['capability'],revoke=o['revoke'])
        self.stdout.write('Scoped capability updated; content-conflict flag retained.')
