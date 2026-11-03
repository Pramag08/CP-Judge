"""D13 author preview: archived native executions with immutable private receipts."""
import uuid
from django import forms
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from judge.models import Contest, ContestProblem, Submission, SubmissionSource, ContestSubmission
from .models import AuthorTest, ContestVersionAdmission, Conflict, Audit
from .policy import require
from .entries import locked_account, locked_contest, payload


def authorize(user, c):
    require(user,c,'settings.edit')
    if user.pk != c.workflow.owner_id:
        if not user.is_superuser: raise PermissionDenied
        require(user,c,'submissions.review')
    from .entries import restricted
    if restricted(user,c) or c.banned_users.filter(user=user).exists(): raise PermissionDenied


def selected(user,key,code):
    c=get_object_or_404(Contest,key=key,workflow__isnull=False)
    authorize(user,c)
    cp=get_object_or_404(ContestProblem,contest=c,problem__code=code)
    return c,cp


def binding(s):
    t=AuthorTest.objects.select_related('approval__version','approval__contest_problem__contest').get(execution=s)
    a=t.approval
    from .publication import verify_native
    from .admission import verify_approval
    verify_native(a.version);verify_approval(a)
    if (not s.is_archived or s.contest_object_id is not None or ContestSubmission.objects.filter(submission=s).exists() or
        s.user.user_id!=t.owner_id or s.problem_id!=a.version.problem_id or s.language_id!=a.runtime_id or
        t.version_digest!=a.version_digest or t.payload_digest!=payload(s.problem.code,s.language_id,s.source.source)):
        raise PermissionDenied('Invalid private author test receipt.')
    # Durable admitted work remains private even after scope/session changes.
    return a


@transaction.atomic
def admit(user,key,code,language,source,request_key,*,generation,auth_hash):
    user,_=locked_account(user,generation,auth_hash);c=locked_contest(key);authorize(user,c)
    cp=get_object_or_404(ContestProblem,contest=c,problem__code=code)
    try:request_key=str(uuid.UUID(str(request_key)))
    except (ValueError,AttributeError):raise PermissionDenied('Valid request key required.')
    digest=payload(code,language,source)
    old=AuthorTest.objects.filter(owner=user,request_key=request_key).select_related('execution','approval__contest_problem').first()
    if old:
        if old.payload_digest!=digest or old.approval.contest_problem_id!=cp.pk:raise PermissionDenied('Request key reused.')
        return old.execution,False
    a=get_object_or_404(ContestVersionAdmission,contest_problem=cp,revoked=False)
    from .publication import verify_native
    from .admission import verify_approval
    try:verify_native(a.version);verify_approval(a)
    except Exception:raise PermissionDenied('Version approval is stale.') from None
    if language!=a.runtime_id or not cp.problem.allowed_languages.filter(pk=language).exists():raise PermissionDenied('Language is not enabled.')
    if not source or len(source.encode())>65536:raise PermissionDenied('Source must be 1–65536 bytes.')
    # Reuse native per-account queue and rate bounds for real execution.
    from django.conf import settings
    from django.utils import timezone
    if (Submission.objects.filter(user=user.profile,status__in=('QU','P','G')).exists() or
        Submission.objects.filter(user=user.profile,date__gte=timezone.now()-settings.DMOJ_SUBMISSION_RATELIMIT_TIMEFRAME).count()>=settings.DMOJ_SUBMISSION_RATELIMIT):
        raise PermissionDenied('Wait for pending work or the submission rate limit.')
    Conflict.objects.get_or_create(user=user,contest=c)
    from judge.models import ContestParticipation
    ContestParticipation.objects.filter(user=user.profile,contest=c,virtual=0).update(virtual=-1)
    from .entries import update_count
    update_count(c)
    s=Submission.objects.create(user=user.profile,problem=cp.problem,language_id=language,is_archived=True)
    SubmissionSource.objects.create(submission=s,source=source)
    AuthorTest.objects.create(execution=s,approval=a,owner=user,request_key=request_key,payload_digest=digest,version_digest=a.version_digest)
    Audit.objects.create(actor=user,action='contest.author_test',scope=str(c.pk),details={'submission':s.pk,'version':a.version_id})
    transaction.on_commit(lambda:dispatch(s.pk))
    return s,True


def dispatch(pk):
    Submission.objects.get(pk=pk).judge(force_judge=True)


class TestForm(forms.Form):
    language=forms.IntegerField(widget=forms.HiddenInput)
    source=forms.CharField(max_length=65536,widget=forms.Textarea(attrs={'rows':16,'cols':80}))
    request_key=forms.UUIDField(widget=forms.HiddenInput)


@require_http_methods(['GET','POST'])
def page(request,contest_key,problem):
    c,cp=selected(request.user,contest_key,problem)
    a=ContestVersionAdmission.objects.filter(contest_problem=cp,revoked=False).select_related('runtime').first()
    if not a:raise PermissionDenied('Select an approved immutable version first.')
    form=TestForm(request.POST if request.method=='POST' else None,initial={'language':a.runtime_id,'request_key':uuid.uuid4()})
    if request.method=='POST' and form.is_valid():
        from .sessions import GENERATION_KEY
        admit(request.user,c.key,problem,form.cleaned_data['language'],form.cleaned_data['source'],form.cleaned_data['request_key'],
              generation=request.session.get(GENERATION_KEY),auth_hash=request.session.get('_auth_user_hash'))
        return redirect('cpj_author_test',contest_key=c.key,problem=problem)
    tests=AuthorTest.objects.filter(approval__contest_problem=cp,owner=request.user).select_related('execution').order_by('-pk')[:50]
    from .probes import headers
    return headers(render(request,'cpjudge/author_test.html',dict(title='Author preview / test mode: '+cp.problem.name,contest=c,cp=cp,runtime=a.runtime,form=form,tests=tests)))
