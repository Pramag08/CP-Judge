"""Minimal explicit admission for a privately allowlisted native contest.

Separate approval metadata never rewrites immutable manifest or judge bytes.
No public publication/contest-management UI or general lifecycle is added.
"""
import hashlib
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from judge.models import Contest,ContestProblem,ContestParticipation,ContestSubmission,Judge
from .models import ContestVersionAdmission,ProblemProbe,Conflict,Audit,ProblemVersion
from .policy import require


def frozen_rules(contest):
    return {'start':contest.start_time.isoformat(),'end':contest.end_time.isoformat(),
        'private':contest.is_private,'organization_private':contest.is_organization_private,
        'visible':contest.is_visible,'rated':contest.is_rated,'format':contest.format_name,
        'config':contest.format_config,'duration':str(contest.time_limit)}


def verify_approval(a):
    from .publication import verify_files,PublicationError
    v=a.version;p=a.probe;s=p.execution;solution=p.solution;c=a.contest_problem.contest
    verify_files(v)
    cases=s.test_cases.all()
    expected=sum(len(x['batched']) if 'batched' in x else 1 for x in v.manifest['test_cases'])
    sha=lambda value:hashlib.sha256(value.encode()).hexdigest()
    if (a.revoked or v.state!='published' or v.problem_id!=a.contest_problem.problem_id or
        v.job.attempt!=v.attempt or v.job.token!=v.token or v.job.status!='succeeded' or
        a.version_digest!=v.digest or a.rules!=frozen_rules(c) or not c.is_private or
        c.is_organization_private or c.is_rated or c.run_pretests_only or a.contest_problem.is_pretested or c.format_name!='cpjudge_icpc_v1' or
        c.format_config!={'penalty':20} or c.time_limit is not None or
        a.contest_problem.points!=1 or a.contest_problem.partial or
        p.version_id!=v.pk or p.problem_digest!=v.digest or p.owner_id!=v.job.owner_id or
        solution.owner_id!=p.owner_id or solution.version_id!=v.pk or
        p.solution_digest!=solution.sha256 or sha(solution.source)!=p.solution_digest or
        sha(s.source.source)!=p.solution_digest or p.runtime_key!=a.runtime.key or
        solution.runtime_id!=a.runtime_id or s.language_id!=a.runtime_id or s.problem_id!=v.problem_id or
        s.user.user_id!=p.owner_id or s.contest_object_id is not None or
        ContestSubmission.objects.filter(submission=s).exists() or
        s.status!='D' or s.result!='AC' or s.case_total<=0 or s.case_points!=s.case_total or cases.count()!=expected or
        cases.exclude(status='AC').exists() or cases.exclude(points=F('total')).exists() or cases.filter(total__lte=0).exists()):
        raise PublicationError('Private contest approval changed or lacks a complete accepted probe.')
    return True


def approvals(version):
    return ContestVersionAdmission.objects.filter(version=version,revoked=False).select_related(
        'version__problem','version__job','probe__solution__runtime','probe__execution__source',
        'probe__execution__user','runtime','contest_problem__contest')


def native_languages(version):
    keys=set(version.manifest['allowed_languages'])
    for a in approvals(version):
        verify_approval(a);keys.add(a.runtime.key)
    return sorted(keys)


@transaction.atomic
def approve(user,version,contest,probe):
    from .publication import authorize,verify_native
    get_user_model().objects.select_for_update().get(pk=user.pk)
    c=Contest.objects.select_for_update().get(pk=contest.pk)
    v=ProblemVersion.objects.select_for_update().select_related('problem','job').get(pk=version.pk)
    authorize(user,v.job_id,v.attempt);require(user,c,'problems.publish')
    if timezone.now()>=c.start_time:raise PermissionDenied('Approve before contest start.')
    verify_native(v)
    cp=ContestProblem.objects.get(contest=c,problem=v.problem)
    if ContestVersionAdmission.objects.filter(contest_problem=cp).exists():raise PermissionDenied('Admission already recorded.')
    probe=ProblemProbe.objects.select_related('solution__runtime').get(pk=probe.pk)
    a=ContestVersionAdmission.objects.create(version=v,contest_problem=cp,probe=probe,runtime=probe.solution.runtime,
        version_digest=v.digest,rules=frozen_rules(c),actor=user)
    verify_approval(a)
    worker=Judge.objects.filter(online=True,is_blocked=False,is_disabled=False,problems=v.problem).first()
    if not worker or not worker.runtimes.filter(pk=a.runtime_id).exists():raise PermissionDenied('Verified worker/runtime must be online.')
    from judge.models import Language
    v.problem.allowed_languages.set(Language.objects.filter(key__in=native_languages(v)))
    # set() needs native Language PKs, never protocol executor strings.
    verify_native(v)
    Audit.objects.create(actor=user,action='version.contest.admit',scope=str(c.pk),
        details={'version':v.pk,'digest':v.digest,'probe':probe.pk,'runtime':a.runtime.key})
    return a


def participant_approval(user,problem,*,submit=False):
    if not user.is_authenticated or not user.is_active:return None
    from .publication import verify_native
    v=ProblemVersion.objects.filter(problem=problem,state='published').first()
    if not v:return None
    try:verify_native(v)
    except Exception:return None
    for a in approvals(v):
        c=a.contest_problem.contest
        if not c.is_visible:continue
        if hasattr(c,'workflow'):
            from .entries import content
            if not content(user,c,submit=submit):continue
            if submit:
                entry=ContestParticipation.objects.filter(registration__user=user,registration__contest=c,registration__status='active',virtual=0).first()
                if not entry:continue
            return a
        if timezone.now()<c.start_time:continue
        if c.banned_users.filter(user=user).exists() or not c.private_contestants.filter(user=user).exists():continue
        entry=ContestParticipation.objects.filter(user__user=user,contest=c,virtual=0).first()
        if not entry or Conflict.objects.filter(user=user,contest=c).exists():continue
        if submit and (timezone.now()>=c.end_time or user.profile.current_contest_id!=entry.pk):continue
        return a
    return None


def validate_execution(s):
    if hasattr(s,'author_test'):
        from .author_tests import binding
        return binding(s)
    if s.contest_object_id and hasattr(s.contest_object,'workflow'):
        from .entries import validate_receipt
        return validate_receipt(s)
    from .publication import verify_native
    try:cs=ContestSubmission.objects.select_related('problem__contest','participation').get(submission=s)
    except ContestSubmission.DoesNotExist:raise PermissionDenied('An official private contest receipt is required.')
    a=ContestVersionAdmission.objects.select_related('version__job','version__problem','runtime',
        'probe__solution','probe__execution','contest_problem__contest').get(contest_problem=cs.problem,revoked=False)
    verify_native(a.version);verify_approval(a)
    c=a.contest_problem.contest
    if (s.problem_id!=a.version.problem_id or s.language_id!=a.runtime_id or
        s.contest_object_id!=c.pk or cs.participation.contest_id!=c.pk or
        cs.participation.user_id!=s.user_id or cs.participation.virtual!=0 or
        not c.start_time<=s.date<c.end_time or not s.user.user.is_active or
        not c.private_contestants.filter(pk=s.user_id).exists() or
        c.banned_users.filter(pk=s.user_id).exists() or Conflict.objects.filter(user_id=s.user.user_id,contest=c).exists()):
        raise PermissionDenied('Private contest receipt does not match its approved version/runtime/entry.')
    return a
