"""Run the declared Polygon main solution in the existing private judge probe path."""
import hashlib
import re
import tempfile
from datetime import timedelta
from pathlib import Path
from defusedxml import ElementTree as ET
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from judge.models import Language, Submission, SubmissionSource
from .models import ProblemVersion, ProbeSolution, ProblemProbe, Audit
from .probes import fingerprint, dispatch


class AutoCheckFailure(ValueError):
    pass


def enqueue(version):
    if ProblemProbe.objects.filter(version=version, solution__name='Automatic reference check').exists():
        return
    ProblemVersion.objects.filter(pk=version.pk).update(auto_check_status='checking',
        auto_check_message='Waiting for a compatible worker and checking the declared reference solution.')
    try:
        from .tasks import automatic_reference_check
        automatic_reference_check.delay(version.pk)
    except Exception:
        ProblemVersion.objects.filter(pk=version.pk).update(auto_check_status='failed',
            auto_check_message='Background check queue unavailable. Restore Celery, then retry the reference check.')


@require_POST
def retry_view(request, version_id):
    from django.http import Http404
    from django.shortcuts import redirect
    from .publication import authorize
    version = ProblemVersion.objects.select_related('job').filter(pk=version_id, state='published').first()
    if version is None:
        raise Http404
    authorize(request.user, version.job_id, version.attempt)
    enqueue(version)
    return redirect('cpj_import_confirm', job_id=version.job_id)


def status(version):
    probe = ProblemProbe.objects.filter(version=version, solution__name='Automatic reference check').select_related('execution').order_by('-pk').first()
    if probe:
        execution = probe.execution
        if execution.status in ('QU', 'P', 'G'):
            return 'Checking problem', 'The reference solution is running on the judge.'
        if execution.status == 'D' and execution.result == 'AC':
            count = sum(len(item['batched']) if 'batched' in item else 1 for item in version.manifest['test_cases'])
            cases = execution.test_cases.all()
            if cases.count() == count and not cases.exclude(status='AC').exists():
                return 'Ready', f'Real judge result: AC on {count} cases. Add this problem to the draft again to bind the result.'
        return 'Failed', f'Real judge result: {execution.result or execution.status}. Fix the reference solution or package and import a new version.'
    if version.auto_check_status == 'checking':
        return 'Checking problem', version.auto_check_message or 'Waiting for a compatible worker.'
    return 'Failed', version.auto_check_message or 'No reference check exists. Publish the private version to start it.'


def run(version_id):
    from compat.convert import required
    from compat.archive import extract_zip
    from .imports import archive_limits, private_root
    from .contest_readiness import check
    version = ProblemVersion.objects.select_related('job__owner', 'job__contest', 'problem').get(pk=version_id)
    if version.state != 'published':
        return
    if ProblemProbe.objects.filter(version=version, solution__name='Automatic reference check').exists():
        return
    try:
        from .publication import authorize
        authorize(version.job.owner, version.job_id, version.attempt)
        package = private_root() / version.job.archive_key
        if not re.fullmatch(r'[a-f0-9]{48}\.zip', version.job.archive_key) or package.is_symlink():
            raise AutoCheckFailure('Stored ZIP is invalid. Upload and import a new package.')
        digest = hashlib.sha256()
        with package.open('rb') as stream:
            for chunk in iter(lambda: stream.read(65536), b''):
                digest.update(chunk)
        if digest.hexdigest() != version.job.package_sha256:
            raise AutoCheckFailure('Stored ZIP changed. Upload and import a new package.')
        with tempfile.TemporaryDirectory(prefix='reference-', dir=private_root()) as directory:
            source_dir = Path(directory) / 'source'
            extract_zip(package, source_dir, archive_limits(version.job))
            main = ET.parse(source_dir / 'problem.xml').getroot().find('assets/solutions/solution[@tag="main"]/source')
            if main is None:
                raise AutoCheckFailure('No declared main reference solution in the Polygon ZIP. Add one and import a new version.')
            match = re.search(r'g\+\+(11|14|17|20|23)$', main.get('type', ''))
            if not match:
                raise AutoCheckFailure('The declared main reference language is unsupported. Use a supported C++ standard and import a new version.')
            if not main.get('path'):
                raise AutoCheckFailure('The declared main reference source is missing. Fix the Polygon ZIP and import a new version.')
            source_path = required(source_dir, main.get('path'))
            if source_path.stat().st_size > 65536:
                raise AutoCheckFailure('The reference source must be 1–65536 bytes. Fix the Polygon ZIP and import a new version.')
            source = source_path.read_text(encoding='utf-8')
            if not source or len(source.encode('utf-8')) > 65536:
                raise AutoCheckFailure('The reference source must be 1–65536 bytes. Fix the Polygon ZIP and import a new version.')
        runtime = Language.objects.get(key='CPP' + match.group(1))
        with transaction.atomic():
            version = ProblemVersion.objects.select_for_update().get(pk=version_id)
            if ProblemProbe.objects.filter(version=version, solution__name='Automatic reference check').exists():
                return
            solution, _ = ProbeSolution.objects.get_or_create(version=version, owner=version.job.owner,
                name='Automatic reference check', defaults={'runtime': runtime, 'source': source, 'sha256': fingerprint(source)})
            if solution.runtime_id != runtime.pk or solution.sha256 != fingerprint(source):
                raise AutoCheckFailure('The reference source changed. Import a new immutable version.')
        check(version.code, runtime.key)
        with transaction.atomic():
            version = ProblemVersion.objects.select_for_update().get(pk=version_id)
            if ProblemProbe.objects.filter(version=version, solution__name='Automatic reference check').exists():
                return
            submission = Submission.objects.create(user=version.job.owner.profile, problem=version.problem,
                language=runtime, is_archived=True)
            SubmissionSource.objects.create(submission=submission, source=source)
            probe = ProblemProbe.objects.create(version=version, solution=solution, owner=version.job.owner,
                execution=submission, problem_digest=version.digest, solution_digest=solution.sha256,
                runtime_key=runtime.key, expires=timezone.now() + timedelta(seconds=120))
            Audit.objects.create(actor=version.job.owner, action='probe.auto', scope=str(version.pk),
                details={'probe': probe.pk, 'runtime': runtime.key})
            transaction.on_commit(lambda: dispatch(probe.pk))
    except Exception as exc:
        # The private task records a concise actionable state; raw diagnostics stay in worker logs.
        message = str(exc)
        if not isinstance(exc, AutoCheckFailure):
            message = 'Compatible worker or reference check unavailable. Verify the worker has this exact version and runtime, then retry the check.'
        ProblemVersion.objects.filter(pk=version_id).update(auto_check_status='failed', auto_check_message=message[:300])
        raise
