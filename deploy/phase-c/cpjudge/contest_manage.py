"""Scoped D01–D06 workflow using native schedules, problems and fixed scoring."""
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from judge.models import Contest, ContestProblem
from .models import (Identity, Grant, Audit, ContestWorkflow, ContestProblemLabel,
                     ProblemVersion, ProblemProbe, ContestVersionAdmission)
from .policy import require, grant_scope, CAPABILITIES
from .publication import verify_native, verify_files

FIXED = dict(format_name='cpjudge_icpc_v1', format_config={'penalty':20}, is_rated=False,
    is_private=True, is_organization_private=False, run_pretests_only=False, time_limit=None,
    scoreboard_visibility=Contest.SCOREBOARD_VISIBLE, use_clarifications=False,
    problem_label_script='', points_precision=0)

class DraftForm(forms.Form):
    key=forms.RegexField(r'^[a-z0-9]{3,20}$',max_length=20,label='Permanent contest ID')
    name=forms.CharField(max_length=100,label='Title')
    description=forms.CharField(max_length=2000,required=False,widget=forms.Textarea(attrs={'rows':4}),label='Description (plain text)')
    display_timezone=forms.CharField(max_length=64,initial='Asia/Kolkata',label='Timezone (IANA name)')
    start_time=forms.CharField(label='Start',widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
    end_time=forms.CharField(label='End',widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))

    def __init__(self,*args,editing=False,**kwargs):
        super().__init__(*args,**kwargs)
        if editing:self.fields.pop('key')
        selected=(self.data.get('display_timezone') if self.is_bound else self.initial.get('display_timezone')) or 'Asia/Kolkata'
        for field in ('start_time','end_time'):
            self.fields[field].help_text=f'Selected timezone: {selected}'

    def clean(self):
        data=super().clean()
        if self.is_bound and set(self.data)-set(self.fields)-{'csrfmiddlewaretoken'}:
            raise ValidationError('Unsupported setting. Only the fixed individual preset is available.')
        try: zone=ZoneInfo(data.get('display_timezone',''))
        except (ZoneInfoNotFoundError,ValueError):
            self.add_error('display_timezone','Use a valid IANA timezone.');return data
        for field in ('start_time','end_time'):
            if field not in data:continue
            try:
                naive=datetime.strptime(data[field].replace('T',' '),'%Y-%m-%d %H:%M')
                aware=naive.replace(tzinfo=zone)
                # Reject ambiguous and nonexistent DST wall times rather than guessing.
                if (aware.utcoffset()!=naive.replace(tzinfo=zone,fold=1).utcoffset() or
                    aware.astimezone(dt_timezone.utc).astimezone(zone).replace(tzinfo=None)!=naive):
                    raise ValueError()
                data[field]=aware.astimezone(dt_timezone.utc)
            except ValueError:self.add_error(field,'Use an unambiguous valid local date/time: YYYY-MM-DD HH:MM.')
        s,e=data.get('start_time'),data.get('end_time')
        if isinstance(s,datetime) and isinstance(e,datetime):
            if s>=e:raise ValidationError('End must be after start.')
            if s<=timezone.now():raise ValidationError('Start must be in the future.')
        return data

class ProblemForm(forms.Form):
    version=forms.ModelChoiceField(queryset=ProblemVersion.objects.none(),label='Problem')
    label=forms.RegexField(r'^[A-Z0-9]{1,10}$',max_length=10,label='Label')
    order=forms.IntegerField(min_value=0,max_value=32767,label='Order (0-based)')
    def __init__(self,user,*args,**kwargs):
        super().__init__(*args,**kwargs)
        scopes=Grant.objects.filter(user=user,capability='problems.publish',revoked=False).values('contest_id')
        self.fields['version'].queryset=ProblemVersion.objects.filter(state='published',job__contest_id__in=scopes).select_related('problem').distinct()
        self.fields['version'].label_from_instance=lambda v:f'{v.problem.name} — revision {v.pk}, imported {v.created:%Y-%m-%d}'


def author(user):
    if not user.is_authenticated or not user.is_active or not Identity.objects.filter(user=user,is_author=True).exists():raise PermissionDenied


def managed(user,key):
    c=get_object_or_404(Contest,key=key,workflow__isnull=False)
    require(user,c,'settings.edit')
    return c


def draft(c):
    if c.is_visible or c.workflow.published_at:raise PermissionDenied('Published contest settings are locked.')


def state(c,now=None):
    now=now or timezone.now()
    if not c.is_visible:return 'Draft',0
    if now<c.start_time:return 'Scheduled',max(0,int((c.start_time-now).total_seconds()))
    if now<c.end_time:return 'Running',max(0,int((c.end_time-now).total_seconds()))
    return 'Ended',0


def eligible(user,c):
    from .entries import restricted
    return (user.is_authenticated and user.is_active and Identity.objects.filter(user=user,canonical_email__isnull=False).exists()
        and not c.banned_users.filter(user=user).exists()
        and not restricted(user,c))


def refresh_languages(c):
    # Reconcile only task-owned draft approvals; preserve other contests' approvals.
    from .admission import native_languages
    from judge.models import Language
    for v in ProblemVersion.objects.filter(problem__contests__contest=c).distinct():
        v.problem.allowed_languages.set(Language.objects.filter(key__in=native_languages(v)))


def rules(c):
    langs=sorted(set(c.contest_problems.values_list('problem__allowed_languages__key',flat=True))-{None})
    return ['Individual ICPC; full AC = 1 solved; partial case points do not solve.',
        '20-minute penalty per prior WA/TLE/MLE/RTE before first AC; CE and unsolved problems add no penalty.',
        'Rank by solved descending, penalty ascending; equal totals share rank (1,1,3).',
        'Common server clock: start inclusive, end exclusive; late entry gives no extra time.',
        'Eligibility: active administrator-provisioned accounts, subject to registration and removal.',
        'Languages: '+(', '.join(langs) or 'None selected')+' (per-problem restrictions apply).',
        'Feedback: case verdict/time/memory; hidden input/output and checker feedback stay private.',
        'Supervised, in-person competition. Register before start or late until the common end; withdraw only before start.']


def readiness(c,*,live=True):
    errors=[]
    if c.start_time<=timezone.now() or c.end_time<=c.start_time:errors.append('Set a future start and an end after start.')
    if any(getattr(c,k)!=v for k,v in FIXED.items()):errors.append('Fixed scoring, clock or feedback settings changed.')
    if c.workflow.eligibility!='provisioned':errors.append('Unsupported eligibility policy.')
    cps=list(c.contest_problems.select_related('problem').order_by('order','pk'))
    if not cps:errors.append('Select at least one immutable problem version.')
    labels=[];orders=[]
    for cp in cps:
        try:
            label=cp.workflow_label.label;labels.append(label);orders.append(cp.order)
            if cp.points!=1 or cp.partial or cp.is_pretested:raise ValueError()
        except Exception:
            errors.append(f'{cp.problem.code}: contest problem label, order or fixed points are missing or invalid.')
            continue
        try:
            v=ProblemVersion.objects.get(problem=cp.problem,state='published')
            verify_files(v)
        except Exception:
            errors.append(f'{cp.problem.code}: published immutable version is missing or stale.')
            continue
        try:
            a=ContestVersionAdmission.objects.get(contest_problem=cp,revoked=False)
        except ContestVersionAdmission.DoesNotExist:
            errors.append(f'{cp.problem.code}: no accepted private probe is bound to this contest problem. Open the import status, wait for the automatic reference check to pass, then add this version again.')
            continue
        try:
            from .admission import verify_approval
            verify_approval(a)
            from .probes import binding
            binding(a.probe)
        except Exception:
            errors.append(f'{cp.problem.code}: accepted private probe or contest approval is stale or incomplete. Recheck the probe and select this version again.')
            continue
        if set(cp.problem.allowed_languages.values_list('key',flat=True))!={a.runtime.key}:
            errors.append(f'{cp.problem.code}: approved language is not enabled for this problem. Select this version again.')
            continue
        try:
            verify_native(v)
        except Exception:
            errors.append(f'{cp.problem.code}: published native problem record or version is stale.')
            continue
        if live:
            try:
                from .contest_readiness import check
                check(v.code,a.runtime.key)
            except Exception:
                errors.append(f'{cp.problem.code}: compatible live worker has not verified this exact version and runtime. Check the private worker installation and readiness service.')
    if len(labels)!=len(set(labels)) or len(orders)!=len(set(orders)):errors.append('Labels and orders must be unique.')
    return errors


@require_http_methods(['GET','POST'])
def create(request):
    author(request.user)
    form=DraftForm(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                data=form.cleaned_data.copy();zone=data.pop('display_timezone')
                c=Contest.objects.create(**data,is_visible=False,**FIXED)
                ContestWorkflow.objects.create(contest=c,owner=request.user,display_timezone=zone)
                for cap in CAPABILITIES-{'clarifications.edit'}:grant_scope(request.user,request.user,c,cap,owner_creation=True)
                Audit.objects.create(actor=request.user,action='contest.create',scope=str(c.pk))
            return redirect('cpj_contest_edit',contest_key=c.key)
        except IntegrityError:form.add_error('key','Contest ID already exists.')
    return render(request,'cpjudge/contest_create.html',{'title':'Create contest','form':form},status=400 if request.method=='POST' else 200)


def listing(request):
    author(request.user)
    cs=Contest.objects.filter(workflow__isnull=False,pk__in=Grant.objects.filter(user=request.user,capability='settings.edit',revoked=False).values('contest_id')).order_by('-start_time')
    return render(request,'cpjudge/contest_list.html',{'title':'My contests','rows':[(c,state(c)[0]) for c in cs]})


@require_http_methods(['GET','POST'])
def edit(request,contest_key):
    c=managed(request.user,contest_key)
    zone=ZoneInfo(c.workflow.display_timezone)
    initial=dict(name=c.name,description=c.description,display_timezone=str(zone),
        start_time=c.start_time.astimezone(zone).strftime('%Y-%m-%dT%H:%M'),end_time=c.end_time.astimezone(zone).strftime('%Y-%m-%dT%H:%M'))
    form=DraftForm(request.POST if request.method=='POST' else None,initial=initial,editing=True)
    if request.method=='POST':
        with transaction.atomic():
            c=Contest.objects.select_for_update().get(pk=c.pk);draft(c)
            if form.is_valid():
                zone=form.cleaned_data.pop('display_timezone')
                for k,v in form.cleaned_data.items():setattr(c,k,v)
                c.save(update_fields=list(form.cleaned_data))
                c.workflow.display_timezone=zone;c.workflow.save(update_fields=['display_timezone'])
                # Admission binds the schedule: editing requires explicit re-selection.
                ContestVersionAdmission.objects.filter(contest_problem__contest=c).update(revoked=True)
                refresh_languages(c)
                Audit.objects.create(actor=request.user,action='contest.edit',scope=str(c.pk))
                return redirect('cpj_contest_edit',contest_key=c.key)
    problems=list(c.contest_problems.select_related('problem').order_by('order','pk'))
    used={cp.workflow_label.label for cp in problems}
    next_label=next((label for label in 'ABCD' if label not in used),'E')
    next_order=max((cp.order for cp in problems),default=-1)+1
    return render(request,'cpjudge/contest_edit.html',dict(title='Manage: '+c.name,contest=c,form=form,
        problem_form=ProblemForm(request.user,initial={'label':next_label,'order':next_order}),
        problems=problems,errors=readiness(c) if not c.is_visible else [],rules=rules(c),
        lifecycle=state(c)[0],visibility='Private' if c.is_private else 'Public'),status=400 if request.method=='POST' else 200)


@require_POST
def problem(request,contest_key):
    c=managed(request.user,contest_key)
    form=ProblemForm(request.user,request.POST)
    if not form.is_valid():return HttpResponse('Invalid version, label or order.',status=400)
    with transaction.atomic():
        c=Contest.objects.select_for_update().get(pk=c.pk);draft(c)
        v=form.cleaned_data['version'];label=form.cleaned_data['label'];order=form.cleaned_data['order']
        require(request.user,v.job.contest,'problems.publish')
        # Validate before changing any native records.
        try:verify_native(v)
        except Exception:return HttpResponse('Version evidence is stale.',status=409)
        others=c.contest_problems.exclude(problem=v.problem)
        if others.filter(order=order).exists() or ContestProblemLabel.objects.filter(contest_problem__in=others,label=label).exists():
            return HttpResponse('Order and label must be unique.',status=409)
        cp,_=ContestProblem.objects.update_or_create(contest=c,problem=v.problem,defaults=dict(order=order,points=1,partial=False,is_pretested=False))
        ContestProblemLabel.objects.update_or_create(contest_problem=cp,defaults={'label':label})
        # Reuse an actual accepted probe; never synthesize execution results.
        found=False
        from .admission import frozen_rules,verify_approval
        from .probes import binding
        for probe in ProblemProbe.objects.filter(version=v,owner=v.job.owner,execution__status='D',execution__result='AC').order_by('-pk'):
            try:
                binding(probe)
                with transaction.atomic():
                    a,_=ContestVersionAdmission.objects.update_or_create(contest_problem=cp,defaults=dict(version=v,probe=probe,runtime=probe.solution.runtime,
                        version_digest=v.digest,rules=frozen_rules(c),actor=request.user,revoked=False))
                    verify_approval(a)
                found=True;break
            except Exception:continue
        if found:
            from .admission import native_languages
            from judge.models import Language
            v.problem.allowed_languages.set(Language.objects.filter(key__in=native_languages(v)))
        if not found:ContestVersionAdmission.objects.filter(contest_problem=cp).update(revoked=True)
        Audit.objects.create(actor=request.user,action='contest.problem',scope=str(c.pk),details={'version':v.pk,'probe_bound':found})
    return redirect('cpj_contest_edit',contest_key=c.key)


@require_POST
def remove(request,contest_key):
    c=managed(request.user,contest_key)
    with transaction.atomic():
        c=Contest.objects.select_for_update().get(pk=c.pk);draft(c)
        cp=get_object_or_404(ContestProblem,contest=c,pk=request.POST.get('problem'))
        ContestVersionAdmission.objects.filter(contest_problem=cp).delete()
        version=ProblemVersion.objects.get(problem=cp.problem)
        cp.delete()
        from .admission import native_languages
        from judge.models import Language
        version.problem.allowed_languages.set(Language.objects.filter(key__in=native_languages(version)))
        Audit.objects.create(actor=request.user,action='contest.problem.remove',scope=str(c.pk))
    return redirect('cpj_contest_edit',contest_key=c.key)


def preview(request,contest_key):
    c=managed(request.user,contest_key)
    from .author_tests import authorize
    authorize(request.user,c)
    return display(request,c,preview=True)


def display(request,c,preview=False):
    current,seconds=state(c);zone=ZoneInfo(c.workflow.display_timezone)
    from .entries import active,content,conflict
    entry=c.registrations.filter(user=request.user).first()
    visible_problems=preview or content(request.user,c)
    return render(request,'cpjudge/contest_preview.html',dict(entry=entry,registration_count=c.user_count,can_register=c.is_visible and timezone.now()<c.end_time and not conflict(request.user,c),can_deregister=bool(entry and entry.status=='active' and timezone.now()<c.start_time),visible_problems=visible_problems,can_submit=content(request.user,c,submit=True),title=('Author preview / test mode: ' if preview else '')+c.name,contest=c,preview=preview,
        state=current,seconds=seconds,server_now=timezone.now().isoformat(),start=c.start_time.astimezone(zone).isoformat(),end=c.end_time.astimezone(zone).isoformat(),
        rules=rules(c),problems=c.contest_problems.select_related('problem').order_by('order','pk') if visible_problems else [],zone=str(zone)))


def overview(request,contest):
    c=get_object_or_404(Contest,key=contest)
    if not hasattr(c,'workflow'):
        from judge.views.contests import ContestDetail
        return ContestDetail.as_view()(request,contest=contest)
    from .native import contest_access
    if not contest_access(request.user,c):raise Http404
    return display(request,c)


@require_POST
def publish(request,contest_key):
    c=managed(request.user,contest_key)
    with transaction.atomic():
        c=Contest.objects.select_for_update().get(pk=c.pk);draft(c)
        errors=readiness(c)
        if errors:return HttpResponse('Publication blocked:\n'+'\n'.join(errors),status=409,content_type='text/plain')
        c.is_visible=True;c.save(update_fields=['is_visible'])
        # Native approval includes visibility; switch it atomically with publication.
        from .admission import frozen_rules
        ContestVersionAdmission.objects.filter(contest_problem__contest=c,revoked=False).update(rules=frozen_rules(c))
        c.workflow.published_at=timezone.now();c.workflow.save(update_fields=['published_at'])
        Audit.objects.create(actor=request.user,action='contest.publish',scope=str(c.pk))
    return redirect('cpj_contest_edit',contest_key=c.key)
