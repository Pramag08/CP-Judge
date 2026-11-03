"""Durable conversion admission and fenced attempt execution; no publication."""
import fcntl,json,os,secrets,shutil,signal,subprocess,sys,time
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .imports import owned,authorize,private_root
from .models import ImportJob
from .compatibility import PUBLIC_REJECTIONS

PUBLIC_ERRORS=frozenset({
    'Conversion service busy. Please retry.',
    'Insufficient private staging space for this conversion. Ask the organizer to free disk space.',
    'Conversion exceeded its runtime limit. Please review package size.',
    'Conversion exceeded a resource limit or stopped unexpectedly. Review package size and retry.',
    'Package validation failed. Check problem.xml, test/answer files, batch mode, checker language and scoring support.',
})


def attempt_path(token):
    import re
    if not re.fullmatch('[a-f0-9]{64}',token):raise ValueError('Invalid attempt token')
    return private_root()/'attempts'/token


def cleanup_attempt(job_id,attempt,token):
    path=attempt_path(token)
    try:owner=json.loads((path/'owner.json').read_text())
    except (OSError,ValueError):return
    if owner=={'job_id':job_id,'attempt':attempt,'token':token}:
        shutil.rmtree(path,ignore_errors=True)


def publish_attempt(job_id,attempt,token):
    try:
        from .tasks import convert_upload
        from celery import current_app
        with current_app.connection_for_write(connect_timeout=3,transport_options={
                'socket_connect_timeout':3,'socket_timeout':3,'retry_on_timeout':False}) as connection:
            convert_upload.apply_async(args=(job_id,attempt,token),queue='cpj_import',retry=False,connection=connection)
    except Exception:
        ImportJob.objects.filter(pk=job_id,attempt=attempt,token=token,status='queued').update(
            status='failed',error='The conversion queue is unavailable. Please retry.',finished_at=timezone.now(),updated=timezone.now())


def queue_conversion(user,job_id):
    with transaction.atomic():
        job=ImportJob.objects.select_for_update().get(pk=owned(user,job_id).pk)
        if job.status in ('queued','running','succeeded','ready','published'):return job
        job.attempt+=1;job.token=secrets.token_hex(32);job.status='queued';job.error='';job.findings={}
        job.queued_at=timezone.now();job.started_at=None;job.finished_at=None;job.save()
        args=(job.pk,job.attempt,job.token)
        transaction.on_commit(lambda:publish_attempt(*args))
        return job


def run_conversion(job,attempt,token):
    root=private_root();lock_path=root/'.conversion.lock'
    fd=os.open(lock_path,os.O_CREAT|os.O_RDWR,0o600)
    acquired=False;process=None;directory=None;created=False
    try:
        deadline=time.monotonic()+5
        while not acquired:
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);acquired=True
            except BlockingIOError:
                if time.monotonic()>=deadline:raise RuntimeError('Conversion service busy. Please retry.')
                time.sleep(.1)
        minimum=int(getattr(settings,'CPJ_CONVERSION_MIN_FREE_BYTES',2*1024**3))
        if minimum<=0 or shutil.disk_usage(root).free<minimum:
            raise RuntimeError('Insufficient private staging space for this conversion. Ask the organizer to free disk space.')
        directory=attempt_path(token);directory.parent.mkdir(mode=0o700,exist_ok=True)
        directory.mkdir(mode=0o700) # Never reuse an attempt's output.
        created=True
        (directory/'owner.json').write_text(json.dumps({'job_id':job.pk,'attempt':attempt,'token':token}))
        (directory/'owner.json').chmod(0o600)
        timeout=int(getattr(settings,'CPJ_CONVERSION_TIMEOUT',120))
        memory=int(getattr(settings,'CPJ_CONVERSION_MEMORY_BYTES',1536*1024**2))
        cpu=int(getattr(settings,'CPJ_CONVERSION_CPU_SECONDS',480))
        file_bytes=int(getattr(settings,'CPJ_CONVERSION_FILE_BYTES',384*1024**2))
        if min(timeout,memory,cpu,file_bytes)<=0:
            raise RuntimeError('Conversion exceeded a resource limit or stopped unexpectedly. Review package size and retry.')
        command=[sys.executable,'-m','cpjudge.convert_runner',str(job.pk),str(directory),str(fd),str(timeout),
                 str(memory),str(cpu),str(file_bytes)]
        with (directory/'runner.log').open('xb') as log:
            os.chmod(log.name,0o600)
            process=subprocess.Popen(command,stdout=log,stderr=log,start_new_session=True,pass_fds=(fd,),env=dict(os.environ,PYTHONUNBUFFERED='1'))
            try:process.wait(timeout=timeout+5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
                raise RuntimeError('Conversion exceeded its runtime limit. Please review package size.')
        if not (directory/'result.json').is_file():
            raise RuntimeError('Conversion exceeded a resource limit or stopped unexpectedly. Review package size and retry.')
        result=json.loads((directory/'result.json').read_text())
        if process.returncode or not result.get('ok'):raise RuntimeError(result.get('error','Conversion failed. Review the package.'))
        return {'converted_directory':'attempts/'+token+'/output','conversion':'succeeded; judging NOT TESTED',
                'slug':result['slug']}
    except Exception:
        if created:shutil.rmtree(directory,ignore_errors=True)
        raise
    finally:
        os.close(fd)


def execute_conversion(job_id,attempt,token):
    owner_id=ImportJob.objects.filter(pk=job_id).values_list('owner_id',flat=True).first()
    if owner_id is None:return False
    with transaction.atomic():
        owner=get_user_model().objects.select_for_update().get(pk=owner_id)
        job=ImportJob.objects.select_for_update().select_related('contest').get(pk=job_id)
        if (job.attempt,job.token,job.status)!=(attempt,token,'queued'):return False
        try:authorize(owner,job.contest)
        except Exception:
            job.status='failed';job.error='Import permission was revoked or the account is unavailable.';job.finished_at=timezone.now();job.save();return False
        job.status='running';job.started_at=timezone.now();job.save(update_fields=['status','started_at','updated'])
    findings={};error=''
    try:findings=run_conversion(job,attempt,token)
    except Exception as exc:
        # Runner errors are bounded public messages; arbitrary framework/OS errors are never exposed.
        public=str(exc)
        error=public if public in PUBLIC_ERRORS | PUBLIC_REJECTIONS else 'Conversion failed. Review problem.xml, test files, checker standard and scoring; then retry.'
    with transaction.atomic():
        owner=get_user_model().objects.select_for_update().get(pk=owner_id)
        current=ImportJob.objects.select_for_update().select_related('contest').get(pk=job_id)
        if (current.attempt,current.token,current.status)!=(attempt,token,'running'):
            cleanup_attempt(job_id,attempt,token);return False
        try:authorize(owner,current.contest)
        except Exception:error='Import permission was revoked or the account is unavailable.'
        current.status='failed' if error else 'succeeded';current.error=error;current.findings={} if error else findings
        current.finished_at=timezone.now();current.save()
    if error:cleanup_attempt(job_id,attempt,token)
    return not bool(error)


def reconcile_imports(now=None,job_id=None):
    """Expire lost queue/running leases; retry is explicit and gets a new token."""
    import datetime
    now=now or timezone.now();count=0
    jobs=ImportJob.objects.filter(status__in=('queued','running'))
    if job_id is not None:jobs=jobs.filter(pk=job_id)
    for job_id in jobs.values_list('pk',flat=True):
        with transaction.atomic():
            job=ImportJob.objects.select_for_update().get(pk=job_id)
            ttl=getattr(settings,'CPJ_CONVERSION_QUEUE_TTL',300) if job.status=='queued' else getattr(settings,'CPJ_CONVERSION_RUNNING_TTL',180)
            since=job.queued_at if job.status=='queued' else job.started_at
            if job.status not in ('queued','running') or not since or since+datetime.timedelta(seconds=ttl)>now:continue
            job.status='failed';job.error='Conversion was interrupted or did not start before its deadline. Please retry.';job.finished_at=now;job.save();count+=1
            # No live converter may be cleaned up; its inherited lock survives Celery loss.
            fd=os.open(private_root()/'.conversion.lock',os.O_CREAT|os.O_RDWR,0o600)
            try:
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if job.token:cleanup_attempt(job.pk,job.attempt,job.token)
            finally:os.close(fd)
    return count
