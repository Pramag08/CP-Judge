from django.core.management.base import BaseCommand
from cpjudge.conversion import reconcile_imports

class Command(BaseCommand):
    help='Mark expired conversion attempts failed so owners can retry. Never publish/rejudge.'
    def handle(self,**options):
        self.stdout.write('Reconciled conversion attempts: '+str(reconcile_imports()))
