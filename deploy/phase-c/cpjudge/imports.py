"""Private single-package upload core, also used by multi-package requests.

No archive-supplied program is invoked. Publication is a separate operation.
"""
import hashlib
import os
from pathlib import Path
import secrets
import tempfile
from contextlib import contextmanager
import re
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from .models import Identity, ImportJob
from .policy import require


def authorize(user, contest=None):
    identity=Identity.objects.filter(user=user).first()
    if not user.is_active or not identity:
        raise PermissionDenied
    if contest is not None:
        require(user,contest,'problems.import')
    elif not identity.is_author:
        raise PermissionDenied


def private_root():
    root=Path(settings.CPJ_IMPORT_ROOT).resolve()
    for name in ('STATIC_ROOT','MEDIA_ROOT'):
        public=getattr(settings,name,None)
        if public and root.is_relative_to(Path(public).resolve()):
            raise RuntimeError('Import storage must be outside static/media roots')
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    root.chmod(0o700)
    return root


def archive_limits():
    from compat.archive import ArchiveLimits
    return ArchiveLimits(**getattr(settings,'CPJ_ARCHIVE_LIMITS',{}))


def upload(user, uploaded, contest=None, *, validate_archive=False):
    authorize(user,contest)
    limits=archive_limits()
    if not uploaded.name.lower().endswith('.zip'):
        raise ValidationError('Select a Polygon .zip package.')
    root=private_root()
    key=secrets.token_hex(24)+'.zip'
    path=root/key
    digest=hashlib.sha256()
    count=0
    created=False
    try:
        with path.open('xb') as dest:
            created=True
            path.chmod(0o600)
            for chunk in uploaded.chunks(chunk_size=65536):
                count+=len(chunk)
                if count>limits.upload_bytes:
                    raise ValidationError('Package exceeds the configured upload limit.')
                digest.update(chunk)
                dest.write(chunk)
        if validate_archive:
            # Bounded ZIP structure validation only. Extraction/conversion are
            # separate later tasks and no archive content is executed here.
            from compat.archive import preflight_directory
            preflight_directory(path,limits)
        with transaction.atomic():
            try:
                with transaction.atomic():
                    job=ImportJob.objects.create(owner=user,contest=contest,package_sha256=digest.hexdigest(),archive_key=key)
            except IntegrityError:
                # Dedupe only within this owner's scope; inaccessible owners never queried.
                job=ImportJob.objects.get(owner=user,package_sha256=digest.hexdigest())
                if job.contest_id != (contest.pk if contest else None):
                    raise ValidationError('This package already has an import in your other contest; use that import explicitly.')
                path.unlink()
        return job
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise


def owned(user, job_id):
    # Uniform absence for unauthorized IDs, including polling/download/retry.
    from django.http import Http404
    job=ImportJob.objects.select_related('owner','contest').filter(pk=job_id,owner=user).first()
    if job is None:
        raise Http404
    authorize(user,job.contest)
    return job


def safe_import_error(exc):
    from .compatibility import rejection_message
    return rejection_message(exc)


@contextmanager
def extracted_upload(user, job_id, *, staging_parent=None):
    """Authorize and validate an original upload in attempt-owned private staging.

    No job state transition, queue, conversion writer or archive program execution.
    The staging tree exists only inside this context, on success or failure.
    """
    from compat.archive import extract_zip
    from compat.convert import read, upstream
    job=owned(user,job_id)
    root=private_root()
    if not re.fullmatch(r'[a-f0-9]{48}\.zip',job.archive_key):
        raise ValidationError('Stored upload reference is invalid. Contact the organizer.')
    archive=root/job.archive_key
    try:
        if archive.is_symlink():
            raise ValueError('Unsafe original upload')
        digest=hashlib.sha256()
        with archive.open('rb') as source:
            for chunk in iter(lambda: source.read(65536),b''):
                digest.update(chunk)
        if digest.hexdigest()!=job.package_sha256:
            raise ValidationError('Stored upload changed. Upload a new package.')
        with tempfile.TemporaryDirectory(prefix='extract-',dir=staging_parent or root) as attempt:
            staging=Path(attempt)/'source'
            result=extract_zip(archive,staging,archive_limits())
            writer,ir=upstream()
            problem,metadata=read(staging,ir)
            bundle=ir.ProblemBundle('polygon',[problem])
            bundle.validate_integrity()
            writer._validate_dmoj_target(bundle,{})
            bundle.ensure_convertible('warn')
            user.refresh_from_db()
            owned(user,job_id)  # Revocation during extraction must prevent use.
            yield staging,dict(result,checker_executor=metadata['checker_executor'])
    except (PermissionDenied,ValidationError):
        raise
    except Exception as exc:
        raise ValidationError(safe_import_error(exc)) from exc


def convert_job(job_id):
    """Called by a bounded native background worker; no public task IDs accepted.

    Locks claim a job, retries are explicit and terminal status survives refresh.
    Crash reconciliation and queue scheduling still require integration acceptance.
    """
    from compat.archive import extract_zip
    from compat.convert import convert
    with transaction.atomic():
        job=ImportJob.objects.select_for_update().select_related('owner','contest').get(pk=job_id)
        authorize(job.owner,job.contest)
        if job.token:
            raise ValidationError('Use the queued conversion workflow for this upload.')
        if job.status in ('processing','ready','published'):
            return
        job.status='processing'
        job.error=''
        job.attempt+=1
        attempt=job.attempt
        job.save(update_fields=['status','error','attempt','updated'])
    try:
        archive=private_root()/job.archive_key
        from compat.convert import file_sha256
        if file_sha256(archive)!=job.package_sha256:
            raise ValidationError('Stored upload changed. Upload a new package.')
        # Configured limits apply before conversion as well as inside its strict extractor.
        with extracted_upload(job.owner,job.pk):
            pass
        output=private_root()/f'job-{job.pk}-attempt-{attempt}'
        slug=convert(archive,output)
        import json
        findings=json.loads((output/'conversion-report.json').read_text())
        findings.update(slug=slug, publication='Not published; statement/readiness/probe gates required',
                        converted_directory=output.name)
        with transaction.atomic():
            job=ImportJob.objects.select_for_update().select_related('owner','contest').get(pk=job_id)
            # Revocation while queued or converting must prevent publication-ready status.
            job.owner.refresh_from_db()
            authorize(job.owner,job.contest)
            job.status='ready'
            job.findings=findings
            job.save(update_fields=['status','findings','updated'])
    except Exception as exc:
        # Do not let a disappearing browser lose the error/status receipt.
        ImportJob.objects.filter(pk=job_id,attempt=attempt).update(status='failed',error=safe_import_error(exc))
        raise
