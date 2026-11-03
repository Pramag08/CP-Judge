"""Private native execution receipts, never official contest submissions."""
import hashlib
from datetime import timedelta
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from judge.models import Language, Submission, SubmissionSource, ContestSubmission
from .models import ProblemVersion, ProbeSolution, ProblemProbe, Audit
from .publication import authorize, verify_native, PublicationError
from .statement import headers as private_headers

def headers(response):
    response=private_headers(response)
    response['Referrer-Policy']='same-origin'
    return response

RUNTIMES = ('CPP11','CPP14','CPP17','CPP20','CPP23')
JOB_SECONDS = 120


def scoped(user, version_id):
    v=ProblemVersion.objects.select_related('job__contest','problem').filter(pk=version_id,job__owner=user).first()
    if not v: raise Http404
    authorize(user,v.job_id,v.attempt)
    verify_native(v)
    return v


def fingerprint(source):
    return hashlib.sha256(source.encode('utf-8')).hexdigest()


def binding(probe, *, dispatch=False):
    v=probe.version
    verify_native(v)
    authorize(probe.owner,v.job_id,v.attempt)
    solution=probe.solution
    s=probe.execution
    if (probe.problem_digest!=v.digest or probe.solution_digest!=solution.sha256 or
        fingerprint(solution.source)!=solution.sha256 or solution.version_id!=v.pk or
        solution.owner_id!=probe.owner_id or solution.runtime.key!=probe.runtime_key or
        s.language.key!=probe.runtime_key or s.problem_id!=v.problem_id or
        s.user.user_id!=probe.owner_id or s.contest_object_id is not None or
        ContestSubmission.objects.filter(submission=s).exists() or
        fingerprint(s.source.source)!=probe.solution_digest or
        (dispatch and timezone.now()>=probe.expires)):
        raise PublicationError('Probe inputs changed or expired.')
    return True


class SolutionForm(forms.Form):
    name=forms.CharField(max_length=80)
    runtime=forms.ChoiceField(choices=[(x,x) for x in RUNTIMES])
    source=forms.CharField(max_length=65536,widget=forms.Textarea(attrs={'rows':8,'cols':70}))
    def clean_source(self):
        source=self.cleaned_data['source']
        if len(source.encode('utf-8'))>65536: raise ValidationError('Source exceeds 64 KiB.')
        return source


def page(request,version_id):
    try: v=scoped(request.user,version_id)
    except PublicationError: return headers(HttpResponse('Version changed; create a new immutable version.',status=409))
    form=SolutionForm()
    if request.method=='POST':
        form=SolutionForm(request.POST)
        if form.is_valid():
            runtime=Language.objects.get(key=form.cleaned_data['runtime'])
            solution=ProbeSolution.objects.create(version=v,owner=request.user,name=form.cleaned_data['name'],
                runtime=runtime,source=form.cleaned_data['source'],sha256=fingerprint(form.cleaned_data['source']))
            Audit.objects.create(actor=request.user,action='probe.solution',scope=str(v.pk),details={'solution':solution.pk,'sha256':solution.sha256,'runtime':runtime.key})
            return redirect('cpj_probes',version_id=v.pk)
    rows=[]
    for probe in ProblemProbe.objects.filter(version=v,owner=request.user).select_related('version__job','version__problem','solution__runtime','execution__source','execution__language','execution__user'):
        s=probe.execution
        try: binding(probe); current=True
        except Exception: current=False
        if s.status in ('QU','P','G') and timezone.now()>=probe.expires:
            transaction.on_commit(lambda pk=probe.pk: expire(pk))
            status='Expired; cancellation requested'
        elif not current: status='Stale inputs; readiness invalid'
        elif s.status in ('QU','P','G'): status={'QU':'Pending verified worker','P':'Compiling','G':'Grading'}[s.status]
        else: status=s.result or s.status
        count=sum(len(x['batched']) if 'batched' in x else 1 for x in v.manifest['test_cases'])
        cases=s.test_cases.all()
        verified=current and s.status=='D' and s.result=='AC' and cases.count()==count and not cases.exclude(status='AC').exists()
        rows.append({'id':probe.pk,'status':status,'verified':verified,'cases':cases.count(),
                     'diagnostic': 'Execution failed; ask the trusted operator for private diagnostics.' if s.status in ('IE','CE','AB') else '',
                     'runtime':probe.runtime_key,'solution':probe.solution.name})
    return headers(render(request,'cpjudge/probes.html',{'title':'Private problem probes','version':v,'form':form,
        'solutions':ProbeSolution.objects.filter(version=v,owner=request.user),'probes':rows}))


@require_POST
def run(request,version_id):
    try:
        v=scoped(request.user,version_id)
        if request.POST.get('digest')!=v.digest: raise PublicationError('Stale version')
        solution=ProbeSolution.objects.select_related('runtime').filter(pk=request.POST.get('solution'),version=v,owner=request.user).first()
        if not solution: raise Http404
        if request.POST.get('solution_digest')!=solution.sha256 or fingerprint(solution.source)!=solution.sha256:
            raise PublicationError('Stale solution')
        if solution.runtime.key not in RUNTIMES: raise PublicationError('Unsupported runtime')
        # Account admission lock serializes per-owner quota. A global DB lock
        # bounds probe backlog across owners without depending on browser state.
        get_user_model().objects.select_for_update().order_by('pk').first()
        active=ProblemProbe.objects.filter(execution__status__in=('QU','P','G'))
        if active.filter(owner=request.user).exists() or active.count()>=2:
            return headers(HttpResponse('A probe is pending. Wait for it to complete.',status=429))
        s=Submission.objects.create(user=request.user.profile,problem=v.problem,language=solution.runtime,is_archived=True)
        SubmissionSource.objects.create(submission=s,source=solution.source)
        probe=ProblemProbe.objects.create(version=v,solution=solution,owner=request.user,execution=s,
            problem_digest=v.digest,solution_digest=solution.sha256,runtime_key=solution.runtime.key,
            expires=timezone.now()+timedelta(seconds=JOB_SECONDS))
        Audit.objects.create(actor=request.user,action='probe.run',scope=str(v.pk),details={'probe':probe.pk,'problem_digest':v.digest,'solution_digest':solution.sha256,'runtime':solution.runtime.key})
        transaction.on_commit(lambda: dispatch(probe.pk))
    except (PublicationError,ValidationError,ValueError):
        return headers(HttpResponse('Stale or unsupported probe inputs. Refresh the private version.',status=409))
    return redirect('cpj_probes',version_id=v.pk)


def dispatch(pk):
    probe=ProblemProbe.objects.select_related('version__job','version__problem','solution__runtime','execution__language','execution__source','execution__user','owner').get(pk=pk)
    try:
        binding(probe,dispatch=True)
        from .tasks import expire_probe
        expire_probe.apply_async(args=[pk],countdown=JOB_SECONDS)
        from judge.judgeapi import judge_submission
        judge_submission(probe.execution)
    except Exception:
        Submission.objects.filter(pk=probe.execution_id,status='QU').update(status='IE',result='IE')


def expire(pk):
    probe=ProblemProbe.objects.select_related('execution').get(pk=pk)
    if timezone.now()>=probe.expires and probe.execution.status in ('QU','P','G'):
        probe.execution.abort()
