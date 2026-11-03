"""Recoverable private version publication. No worker install, assignment or probes."""
import fcntl,json,logging,os,re,secrets,shutil,tempfile,zipfile
from contextlib import contextmanager
from pathlib import Path
import yaml
from lxml import html
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from django.http import Http404,HttpResponse
from django.shortcuts import redirect,render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from judge.models import Problem,ProblemGroup,LanguageLimit,ProblemData
from tools.site_problem import file_manifest,canonical_digest,install_directory
from tools.verify_install import verify as verify_conversion
from .models import ProblemVersion,ImportJob,Audit,Identity
from .imports import private_root,owned
from .policy import require,allowed
from .compatibility import preview
from .conversion import attempt_path
from .statement import build,headers

CSS='''#statement-preview .section-title,#statement-preview .title{font-weight:bold;margin-top:1em}
#statement-preview pre{white-space:pre-wrap;border:1px solid #ccc;padding:0.6em}
#statement-preview img{max-width:100%;height:auto}
#statement-preview .tex-font-style-bf{font-weight:bold}
#statement-preview .tex-font-style-it{font-style:italic}
'''

class PublicationError(ValueError):pass


def root():
    parent=private_root()/'publications'
    if parent.is_symlink():raise PublicationError('Invalid publication root')
    parent.mkdir(mode=0o700,exist_ok=True);parent.chmod(0o700)
    return parent


def destination(version):
    if not re.fullmatch(r'pv9[0-9]{17}',version.code):raise PublicationError('Invalid version code')
    return root()/version.code


def authorize(user,job_id,attempt,admission=None):
    if admission is not None:
        generation=Identity.objects.get(user=user).generation
        if admission!=(generation,user.get_session_auth_hash()):raise PermissionDenied('The publication session was replaced.')
    job=owned(user,job_id)
    if not job.contest_id:raise PermissionDenied
    require(user,job.contest,'problems.publish')
    if job.status!='succeeded' or job.attempt!=attempt:raise PublicationError('A current successful conversion is required.')
    return job


def intent(user,job_id,attempt,admission=None):
    with transaction.atomic(durable=True):
        user=get_user_model().objects.select_for_update().get(pk=user.pk)
        job=ImportJob.objects.select_for_update().get(pk=authorize(user,job_id,attempt,admission).pk)
        version=ProblemVersion.objects.filter(job=job,attempt=attempt).first()
        if version:
            if version.token!=job.token:raise PublicationError('Attempt changed')
            return version
        if not preview(job):raise PublicationError('Conversion receipt unavailable')
        # Unique random placeholder is replaced before this transaction commits.
        version=ProblemVersion.objects.create(job=job,attempt=attempt,token=job.token,code=secrets.token_hex(10))
        if version.pk>=10**17:raise PublicationError('Version code space exhausted')
        version.code='pv'+str(9*10**17+version.pk)
        if Problem.objects.filter(code=version.code).exists() or destination(version).exists():
            raise PublicationError('Version identity collision; no existing data adopted')
        version.save(update_fields=['code'])
        return version


@contextmanager
def version_lock(version):
    locks=root()/'.locks';locks.mkdir(mode=0o700,exist_ok=True)
    fd=os.open(locks/(str(version.pk)+'.lock'),os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise PublicationError('Publication in progress. Refresh and retry.')
        yield
    finally:os.close(fd)


def validate_config(config):
    # Accept only the pinned writer's strict batch shape, including per-case
    # keys. Extra native generator/checker hooks must not gain import semantics.
    if set(config)!={'archive','test_cases','checker','time_limit','memory_limit','short_circuit'} or config['archive']!='data.zip':
        raise PublicationError('Unsupported native configuration fields')
    checker=config['checker']
    if set(checker)!={'name','args'} or set(checker['args'])!={'files','lang','type'}:
        raise PublicationError('Unsupported native checker fields')
    for entry in config['test_cases']:
        if 'batched' in entry:
            if not {'batched','points'}<=set(entry) or set(entry)-{'batched','points','dependencies'}:
                raise PublicationError('Unsupported native group fields')
            if any(set(case)!={'in','out'} for case in entry['batched']):raise PublicationError('Unsupported native case fields')
        elif set(entry)!={'in','out','points'}:raise PublicationError('Unsupported native case fields')


def check_mapping(job,output,config):
    """Extend B05's independent source/config verification with exact case groups."""
    from defusedxml import ElementTree as ET
    verified=verify_conversion(private_root()/job.archive_key,output)
    if verified['source_sha256']!=job.package_sha256:raise PublicationError('Package digest mismatch')
    with zipfile.ZipFile(private_root()/job.archive_key) as archive:
        doc=ET.fromstring(archive.read('problem.xml'));ts=doc.find('judging/testset')
        tests=ts.findall('tests/test');groups=ts.findall('groups/group')
        entries=config['test_cases']
        if groups:
            if len(groups)!=len(entries):raise PublicationError('Group count mismatch')
            sets=[([i for i,t in enumerate(tests,1) if t.get('group')==g.get('name')],entry['batched']) for g,entry in zip(groups,entries)]
        else:sets=[(list(range(1,len(tests)+1)),entries)]
        for numbers,cases in sets:
            if len(numbers)!=len(cases):raise PublicationError('Group membership mismatch')
            for n,case in zip(numbers,cases):
                if case.get('in')!=f'{n}.in' or case.get('out')!=f'{n}.out':raise PublicationError('Case order mismatch')
                if not groups and case.get('points')!=1:raise PublicationError('Case points mismatch')
        language=doc.find('assets/checker/source').get('type','')
        match=re.search(r'g\+\+(11|14|17|20|23)$',language)
        if not match or config['checker']['args']['lang']!='CPP'+match.group(1):raise PublicationError('Checker standard mismatch')
        if config['checker']['name']!='bridged' or config['checker']['args']['type']!='testlib' or config['short_circuit'] is not False:
            raise PublicationError('Unsupported native configuration')
    return verified


def prepare(version,stage):
    job=version.job
    details=preview(job)
    if not details:raise PublicationError('Conversion receipt unavailable')
    output=attempt_path(job.token)/'output';source=output/job.findings['slug']
    # Preparation and immutable installation each copy the native files once.
    # Preserve a configured free-space reserve rather than starting a half-staged version.
    native_bytes=sum((source/name).stat().st_size for name in ('init.yml','data.zip'))
    reserve=int(getattr(settings,'CPJ_PUBLICATION_RESERVE_BYTES',512*1024**2))
    if reserve<=0 or shutil.disk_usage(root()).free < 2*native_bytes+reserve:
        raise PublicationError('Insufficient private staging space for publication')
    config=yaml.safe_load((source/'init.yml').read_text());validate_config(config)
    fragment,assets,notices=build(job)  # C09 validates source digest and actual asset types.
    check_mapping(job,output,config)
    # Validate all source paths before selecting native judge files (no raw HTML/ZIP).
    file_manifest(source)
    names=['init.yml','data.zip',*config['checker']['args']['files']]
    for name in names:
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+',name) or name in ('.','..'):raise PublicationError('Unsafe native filename')
        shutil.copyfile(source/name,stage/name)
    samples=source/'sidecar/samples'
    if samples.exists():shutil.copytree(samples,stage/'sidecar/samples')
    doc=html.fragment_fromstring(fragment,create_parent='div')
    for node in doc.xpath('.//img'):
        key=node.get('src').rsplit('/',1)[-1]
        if key not in assets:raise PublicationError('Unapproved presentation image')
        node.set('src',reverse('cpj_version_asset',kwargs={'problem':version.code,'asset':key}))
    description='<div id="statement-preview">'+html.tostring(doc,encoding='unicode',with_tail=False)+'</div>'
    folder=stage/'presentation';folder.mkdir()
    (folder/'statement.html').write_text(description)
    (folder/'statement.css').write_text(CSS)
    for key,data in assets.items():(folder/key).write_bytes(data)
    points=sum(c.get('points',1) for c in config['test_cases'])
    # No submission-language requirement is inferred from the checker standard.
    fields={'name':details['name'],'description':description,'time_limit':config['time_limit'],
        'memory_limit':config['memory_limit'],'short_circuit':config['short_circuit'],
        'points':points,'partial':True,'is_public':False,'is_manually_managed':True,
        'is_organization_private':False}
    return {'schema':1,'code':version.code,'job_id':job.pk,'attempt':version.attempt,
        'token':version.token,'package_sha256':job.package_sha256,
        'converter_pin':'41ce3afcedf6c02793b308ba2e6ddb2ea5f82134',
        'fields':fields,'allowed_languages':[], 'checker':config['checker'],
        'test_cases':config['test_cases'],'samples':details['sample_count'],
        'notices':notices,'files':file_manifest(stage)}


def verify_files(version):
    manifest=version.manifest
    if not manifest or canonical_digest(manifest)!=version.digest or manifest['code']!=version.code:
        raise PublicationError('Invalid publication receipt')
    if file_manifest(destination(version))!=manifest['files']:raise PublicationError('Installed files changed')
    config=yaml.safe_load((destination(version)/'init.yml').read_text());validate_config(config)
    fields=manifest['fields']
    if (config['time_limit']!=fields['time_limit'] or config['memory_limit']!=fields['memory_limit'] or
        config['short_circuit']!=fields['short_circuit'] or config['checker']!=manifest['checker'] or
        config['test_cases']!=manifest['test_cases']):raise PublicationError('Native configuration changed')
    if (destination(version)/'presentation/statement.html').read_text()!=fields['description']:
        raise PublicationError('Statement receipt mismatch')
    return True


def verify_native(version):
    verify_files(version)
    problem=version.problem
    if version.state!='published' or problem is None:raise PublicationError('Version unfinished')
    if problem.code!=version.code or any(getattr(problem,k)!=v for k,v in version.manifest['fields'].items()):
        raise PublicationError('Native record changed')
    from .admission import native_languages
    if list(problem.allowed_languages.order_by('key').values_list('key',flat=True))!=native_languages(version):
        raise PublicationError('Submission languages changed')
    if LanguageLimit.objects.filter(problem=problem).exists() or ProblemData.objects.filter(problem=problem).exists():
        raise PublicationError('Native data overrides forbidden')
    if problem.group.name!='localpolygon' or problem.group.full_name!='Private Polygon imports':raise PublicationError('Category changed')
    return True


def finalize(user,version,admission=None):
    with transaction.atomic(durable=True):
        user=get_user_model().objects.select_for_update().get(pk=user.pk)
        job=ImportJob.objects.select_for_update().get(pk=authorize(user,version.job_id,version.attempt,admission).pk)
        current=ProblemVersion.objects.select_for_update().get(pk=version.pk)
        if current.token!=job.token:raise PublicationError('Attempt changed')
        if current.state=='published':verify_native(current);return current
        verify_files(current)
        if Problem.objects.filter(code=current.code).exists():raise PublicationError('Unregistered native code collision')
        category,_=ProblemGroup.objects.get_or_create(name='localpolygon',defaults={'full_name':'Private Polygon imports'})
        if category.full_name!='Private Polygon imports':raise PublicationError('Category collision')
        problem=Problem(code=current.code,group=category,**current.manifest['fields'])
        problem.full_clean(exclude=['description']);problem.save()
        problem.authors.add(user.profile)
        current.problem=problem;current.state='published';current.published=timezone.now();current.save()
        Audit.objects.create(actor=user,subject=user,action='problem.publish',scope=str(job.contest_id),
            details={'version':current.pk,'job':job.pk,'attempt':job.attempt,'digest':current.digest})
        verify_native(current)
        return current


def publish(user,job_id,attempt,admission=None):
    version=intent(user,job_id,attempt,admission)  # Durable intent precedes any final filesystem name.
    with version_lock(version):
        version.refresh_from_db()
        job=authorize(user,job_id,attempt,admission)
        if version.token!=job.token:raise PublicationError('Attempt changed')
        if version.state=='published':verify_native(version);return version
        if destination(version).exists():
            verify_files(version)  # Recover rename-before-DB-commit without overwriting bytes.
        else:
            with tempfile.TemporaryDirectory(prefix='.prepare-'+str(version.pk)+'-',dir=root()) as temp:
                stage=Path(temp);manifest=prepare(version,stage);digest=canonical_digest(manifest)
                with transaction.atomic(durable=True):
                    current=ProblemVersion.objects.select_for_update().get(pk=version.pk)
                    if current.manifest and (current.manifest!=manifest or current.digest!=digest):
                        raise PublicationError('Frozen publication input changed')
                    current.manifest=manifest;current.digest=digest;current.save(update_fields=['manifest','digest'])
                version.refresh_from_db()
                install_directory(stage,root(),version.code,manifest['files'],durable=True)
        fd=os.open(root(),os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        return finalize(user,version,admission)


@transaction.non_atomic_requests
@require_POST
def publish_view(request,job_id):
    try:attempt=int(request.POST.get('attempt',''))
    except ValueError:return headers(HttpResponse('Invalid conversion attempt.',status=400))
    from .sessions import GENERATION_KEY
    admission=(request.session.get(GENERATION_KEY),request.session.get('_auth_user_hash'))
    try:authorize(request.user,job_id,attempt,admission)
    except PublicationError:return headers(HttpResponse('A current successful conversion is required.',status=409))
    try:version=publish(request.user,job_id,attempt,admission)
    except (PermissionDenied,Http404):raise
    except Exception:
        logging.getLogger(__name__).exception("Private publication failed for import %s attempt %s",job_id,attempt)
        # Keep the receipt and owned immutable files for retry/reconciliation.
        return headers(render(request,'cpjudge/publication_error.html',{
            'title':'Publication incomplete','job_id':job_id},status=409))
    return redirect('cpj_import_confirm',job_id=job_id)


def published_access(user,problem):
    try:
        version=ProblemVersion.objects.select_related('problem','job__contest').get(problem=problem,state='published')
        owned(user,version.job_id);require(user,version.job.contest,'problems.publish')
        verify_native(version)
        return True
    except (ProblemVersion.DoesNotExist,PermissionDenied,Http404,ValueError,OSError,AssertionError,KeyError):return False


def published_description(value,code):
    from markupsafe import Markup
    version=ProblemVersion.objects.select_related('problem').get(code=code,state='published')
    verify_native(version)
    if value!=version.manifest['fields']['description']:raise PublicationError('Description changed')
    from markupsafe import escape
    notices=''.join('<p class="statement-notice">'+str(escape(n))+'</p>' for n in version.manifest['notices'])
    return Markup('<p>Private installed version. Participant submissions require separate verified contest admission.</p>'+notices+value)


def version_asset(request,problem,asset):
    obj=Problem.objects.filter(code=problem).first()
    from .native import problem_access
    if not obj or not problem_access(request.user,obj):raise Http404
    if asset!='statement.css' and not re.fullmatch(r'[a-f0-9]{64}\.png',asset):raise Http404
    version=ProblemVersion.objects.get(problem=obj,state='published')
    verify_native(version)
    path=destination(version)/'presentation'/asset
    if not path.is_file():raise Http404
    response=headers(HttpResponse(path.read_bytes(),content_type='text/css; charset=utf-8' if asset=='statement.css' else 'image/png'))
    response['Content-Security-Policy']="default-src 'none'; sandbox"
    return response
