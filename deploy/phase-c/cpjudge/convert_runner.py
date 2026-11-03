"""Trusted bounded child. Only converter Python code is invoked, never ZIP programs."""
import json,os,resource,signal,sys
from pathlib import Path

def main():
    job_id,directory,lock_fd,timeout=int(sys.argv[1]),Path(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
    memory,cpu,file_bytes=map(int,sys.argv[5:8])
    os.umask(0o077)
    import tempfile
    tempfile.tempdir=str(directory)
    resource.setrlimit(resource.RLIMIT_AS,(memory,memory))
    resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu))
    resource.setrlimit(resource.RLIMIT_FSIZE,(file_bytes,file_bytes))
    resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
    def expired(*args):raise TimeoutError('Conversion runtime exceeded')
    signal.signal(signal.SIGALRM,expired);signal.alarm(timeout)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','dmoj.settings')
    os.environ['PCC_ROOT']='/tmp/cpj-pcc'
    # The trusted pinned checkout is owned by the deployment user, not HTTP root.
    os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0='/tmp/cpj-pcc')
    result={'ok':False,'error':'Package validation failed. Check problem.xml, test/answer files, batch mode, checker language and scoring support.'}
    try:
        import django;django.setup()
        from django.conf import settings
        from cpjudge.models import ImportJob
        from cpjudge.imports import extracted_upload
        from compat import convert as converter
        from compat.archive import extract_zip,ArchiveLimits
        # Apply the same strict bounds to converter-owned extraction passes.
        converter.extract=lambda archive,target,limits=None:extract_zip(archive,target,limits or ArchiveLimits(**settings.CPJ_ARCHIVE_LIMITS))
        job=ImportJob.objects.select_related('owner').get(pk=job_id)
        with extracted_upload(job.owner,job.pk,staging_parent=directory):pass
        slug=converter.convert(Path(settings.CPJ_IMPORT_ROOT)/job.archive_key,directory/'output')
        result={'ok':True,'slug':slug}
    except Exception as exc:
        from cpjudge.compatibility import PUBLIC_REJECTIONS, rejection_message
        from django.core.exceptions import ValidationError
        # C06 already maps extraction/reader failures to fixed public messages.
        message = exc.messages[0] if isinstance(exc, ValidationError) and len(exc.messages)==1 else ''
        result['error'] = message if message in PUBLIC_REJECTIONS else rejection_message(exc)
    finally:
        (directory/'result.json').write_text(json.dumps(result))
    return 0 if result['ok'] else 1

if __name__=='__main__':sys.exit(main())
