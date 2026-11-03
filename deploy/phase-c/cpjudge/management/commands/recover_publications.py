from django.core.management.base import BaseCommand,CommandError
from cpjudge.models import ProblemVersion
from cpjudge.publication import publish

class Command(BaseCommand):
    help='Resume one persisted private publication intent; rechecks its owner and current scope. No worker install/probe.'
    def add_arguments(self,parser):parser.add_argument('version',type=int)
    def handle(self,*args,**options):
        try:
            version=ProblemVersion.objects.select_related('job__owner').get(pk=options['version'])
            result=publish(version.job.owner,version.job_id,version.attempt)
        except Exception as exc:raise CommandError('Publication could not be recovered; inspect the private receipt and current author scope.') from exc
        self.stdout.write('Recovered private version '+result.code+'; submissions disabled.')
