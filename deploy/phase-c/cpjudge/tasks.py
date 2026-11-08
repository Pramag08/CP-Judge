"""Scoped private roster exports and fail-closed legacy management tasks."""
import csv
import io
import os
from pathlib import Path
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction
from .models import ExportJob, Identity
from .policy import require, roster

EXPORT_ROOT=Path('/app/private-cpj-exports')

@shared_task(acks_late=True,reject_on_worker_lost=True)
def convert_upload(job_id,attempt,token):
    from .conversion import execute_conversion
    return execute_conversion(job_id,attempt,token)

@shared_task(acks_late=True, reject_on_worker_lost=True)
def automatic_reference_check(version_id):
    from .auto_probe import run
    run(version_id)

def export_authorized(job):
    user=get_user_model().objects.get(pk=job.owner_id)
    identity=Identity.objects.get(user=user)
    if not user.is_active or identity.generation!=job.generation:
        raise PermissionDenied
    require(user,job.contest,'roster.export')
    return user


def sheet(value):
    value=str(value or '')
    return "'"+value if value.lstrip().startswith(('=','+','-','@','\t','\r')) else value

@shared_task
def export_roster(job_id):
    job=ExportJob.objects.select_related('contest').get(pk=job_id)
    try:
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=job.owner_id)
            user=export_authorized(job)
            stream=io.StringIO();writer=csv.writer(stream)
            writer.writerow(['College ID / legacy handle','First name','Last name','Email'])
            # Export capability is checked independently of roster.read.
            for row in roster(user,job.contest,export=True):
                writer.writerow([sheet(v) for v in row.values()])
            EXPORT_ROOT.mkdir(mode=0o700,parents=True,exist_ok=True)
            path=EXPORT_ROOT/(job.token+'.csv')
            # Repeat execution is idempotent; bytes are never served without current auth.
            temporary=EXPORT_ROOT/(job.token+'.tmp')
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
            with os.fdopen(fd,'w') as output:output.write(stream.getvalue())
            temporary.replace(path)
            job.status='ready';job.save(update_fields=['status'])
    except PermissionDenied:
        ExportJob.objects.filter(pk=job_id).update(status='denied')
        raise


def guard_native_tasks():
    # Legacy management tasks lack authenticated owner/generation/scope context.
    # Reject even if injected directly into Celery. Native judging/result tasks
    # and ordinary participation.recompute_results remain untouched.
    from judge.tasks import contest, submission, user
    def denied(*args,**kwargs):raise PermissionDenied('Use a scoped management workflow.')
    for module,names in ((contest,('run_moss','rescore_contest')),
        (submission,('rejudge_problem_filter','rescore_problem')),(user,('prepare_user_data',))):
        for name in names:
            getattr(module,name).run=denied


@shared_task
def expire_probe(pk):
    from .probes import expire
    expire(pk)
