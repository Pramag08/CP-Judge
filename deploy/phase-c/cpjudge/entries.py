"""D07–D09/D11: shared contest lock for entry changes and official admission."""
import hashlib,json,uuid
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404,HttpResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from django.views.decorators.http import require_POST
from judge.models import Contest,ContestParticipation,ContestProblem,Submission,SubmissionSource,ContestSubmission
from .models import ContestEntry,ContestReceipt,ContestVersionAdmission,Conflict,Identity,Audit
from .policy import require,allowed


def server_now():return timezone.now()


def restricted(user,contest):
    return ContestEntry.objects.filter(user=user,contest=contest,status__in=('removed','dq')).exists()


def conflict(user,contest):
    from .models import ProblemVersion, AuthorTest, ProbeSolution
    problems=contest.contest_problems.values('problem_id')
    return (Conflict.objects.filter(user=user,contest=contest).exists() or
        getattr(getattr(contest,'workflow',None),'owner_id',None)==user.pk or
        ProblemVersion.objects.filter(problem_id__in=problems,job__owner=user).exists() or
        ProbeSolution.objects.filter(version__problem_id__in=problems,owner=user).exists() or
        AuthorTest.objects.filter(approval__version__problem_id__in=problems,owner=user).exists() or
        contest.problems.filter(Q(authors__user=user)|Q(testers__user=user)|Q(curators__user=user)).exists())


def active(user,contest):
    return ContestEntry.objects.filter(user=user,contest=contest,status='active',participation__virtual=0,participation__is_disqualified=False).first()


def content(user,contest,*,submit=False):
    from .contest_manage import eligible
    if not eligible(user,contest) or restricted(user,contest) or not contest.is_visible:return False
    now=server_now()
    if now<contest.start_time:return False
    if submit:return now<contest.end_time and bool(active(user,contest)) and not conflict(user,contest)
    return now>=contest.end_time or bool(active(user,contest))


def locked_account(user,generation=None,auth_hash=None):
    if not user.is_authenticated:raise PermissionDenied
    user=get_user_model().objects.select_for_update().get(pk=user.pk)
    identity=Identity.objects.get(user=user)
    if not user.is_active or not identity.canonical_email:raise PermissionDenied
    if generation is not None and (identity.generation!=generation or user.get_session_auth_hash()!=auth_hash):raise PermissionDenied('Session was replaced.')
    return user,identity


def locked_contest(key):
    return get_object_or_404(Contest.objects.select_for_update(),key=key,workflow__isnull=False)


def entry_allowed(user,c):
    from .contest_manage import eligible
    if not c.is_visible or not eligible(user,c) or restricted(user,c):raise PermissionDenied
    if conflict(user,c):raise PermissionDenied('Contest authors and reviewers cannot register officially; author testing is separate.')


@transaction.atomic
def register(user,key):
    user,_=locked_account(user);c=locked_contest(key);entry_allowed(user,c)
    now=server_now()  # Sample only after the serialization lock.
    if now>=c.end_time:raise PermissionDenied('Registration has ended.')
    entry=ContestEntry.objects.select_for_update().filter(user=user,contest=c).first()
    if not entry:
        participation,_=ContestParticipation.objects.get_or_create(user=user.profile,contest=c,virtual=0,defaults={'real_start':now})
        if participation.is_disqualified:raise PermissionDenied
        entry=ContestEntry.objects.create(user=user,contest=c,participation=participation,registered_at=now,changed_at=now)
        Audit.objects.create(actor=user,subject=user,action='entry.register',scope=str(c.pk))
    elif entry.status=='withdrawn':
        entry.status='active';entry.registered_at=now;entry.changed_at=now;entry.save(update_fields=['status','registered_at','changed_at'])
        Audit.objects.create(actor=user,subject=user,action='entry.register',scope=str(c.pk))
    elif entry.status!='active':raise PermissionDenied
    if entry.participation.virtual!=0:raise PermissionDenied('Unranked entry.')
    c.private_contestants.add(user.profile)
    if now>=c.start_time:
        # Native navigation context is convenient, never registration authority.
        profile=user.profile;profile.current_contest_id=entry.participation_id;profile.save(update_fields=['current_contest'])
    update_count(c)
    return entry


@transaction.atomic
def deregister(user,key):
    user,_=locked_account(user);c=locked_contest(key);entry_allowed(user,c)
    now=server_now()
    if now>=c.start_time:raise PermissionDenied('Deregistration closes at contest start.')
    entry=ContestEntry.objects.select_for_update().filter(user=user,contest=c).first()
    if entry and entry.status=='active':
        entry.status='withdrawn';entry.changed_at=now;entry.save(update_fields=['status','changed_at'])
        c.private_contestants.remove(user.profile)
        from judge.models import Profile
        Profile.objects.filter(user=user,current_contest=entry.participation).update(current_contest=None)
        Audit.objects.create(actor=user,subject=user,action='entry.withdraw',scope=str(c.pk))
    update_count(c)
    return entry


def update_count(c):
    # Native cached count excludes withdrawal, removal, DQ and content conflicts.
    count=ContestEntry.objects.filter(contest=c,status='active',participation__virtual=0,participation__is_disqualified=False).exclude(user_id__in=Conflict.objects.filter(contest=c).values('user_id')).count()
    Contest.objects.filter(pk=c.pk).update(user_count=count)


@require_POST
def register_view(request,contest):
    register(request.user,contest);return redirect('contest_view',contest=contest)


@require_POST
def deregister_view(request,contest):
    deregister(request.user,contest);return redirect('contest_view',contest=contest)


@require_POST
def leave_view(request,contest):
    c=get_object_or_404(Contest,key=contest,workflow__isnull=False)
    # Leaving clears navigation only, even before start. Never withdraw silently.
    from judge.models import Profile
    Profile.objects.filter(user=request.user,current_contest__contest=c).update(current_contest=None)
    return redirect('contest_view',contest=contest)


@transaction.atomic
def sanction(actor,key,entry_id,action,reason,*,generation=None,auth_hash=None):
    if action not in ('remove','dq'):raise PermissionDenied
    reason=reason.strip()
    if not reason or len(reason)>500:raise PermissionDenied('A reason of 1–500 characters is required.')
    # Audit.subject has a User FK, so lock BOTH accounts before the contest.
    # The HTTP path releases its initial session-check transaction; this service
    # rechecks generation/hash after obtaining account locks in primary-key order.
    preliminary=get_object_or_404(Contest,key=key,workflow__isnull=False)
    require(actor,preliminary,'entrants.manage')
    target=get_object_or_404(ContestEntry,pk=entry_id,contest__key=key)
    list(get_user_model().objects.select_for_update().filter(pk__in={actor.pk,target.user_id}).order_by('pk'))
    actor,_=locked_account(actor,generation,auth_hash)
    c=locked_contest(key);require(actor,c,'entrants.manage')
    if restricted(actor,c) or c.banned_users.filter(user=actor).exists():raise PermissionDenied
    entry=get_object_or_404(ContestEntry.objects.select_for_update(),pk=entry_id,contest=c)
    if entry.status=='withdrawn':raise PermissionDenied('This entry withdrew.')
    target='dq' if action=='dq' or entry.status=='dq' else 'removed'
    if entry.status!=target:
        entry.status=target;entry.changed_at=server_now();entry.save(update_fields=['status','changed_at'])
        if target=='dq':ContestParticipation.objects.filter(pk=entry.participation_id).update(is_disqualified=True)
        c.banned_users.add(entry.user.profile)
        from judge.models import Profile
        Profile.objects.filter(user=entry.user,current_contest=entry.participation).update(current_contest=None)
        Audit.objects.create(actor=actor,subject=entry.user,action='entry.'+action,scope=str(c.pk),details={'entry':entry.pk,'reason':reason})
    update_count(c)
    return entry


@require_POST
def sanction_view(request,contest,entry_id):
    from .sessions import GENERATION_KEY
    sanction(request.user,contest,entry_id,request.POST.get('action',''),request.POST.get('reason',''),generation=request.session.get(GENERATION_KEY),auth_hash=request.session.get('_auth_user_hash'))
    return redirect('cpj_roster',contest=contest)


def roster(request,c):
    require(request.user,c,'roster.read')
    rows=ContestEntry.objects.filter(contest=c).select_related('user','participation').order_by('pk')
    return render(request,'cpjudge/entry_roster.html',dict(title='Roster: '+c.name,contest=c,rows=rows,can_manage=allowed(request.user,c,'entrants.manage')))


def payload(code,language,source):
    return hashlib.sha256(json.dumps([code,language,source],ensure_ascii=True,separators=(',',':')).encode()).hexdigest()


@transaction.atomic
def admit(user,key,code,language,source,request_key,*,generation,auth_hash):
    user,identity=locked_account(user,generation,auth_hash);c=locked_contest(key);entry_allowed(user,c)
    entry=get_object_or_404(ContestEntry.objects.select_for_update(),user=user,contest=c,status='active')
    if entry.participation.virtual!=0 or entry.participation.is_disqualified:raise PermissionDenied
    try:request_key=str(uuid.UUID(str(request_key)))
    except (ValueError,AttributeError):raise PermissionDenied('Valid request key required.')
    digest=payload(code,language,source)
    previous=ContestReceipt.objects.filter(entry=entry,request_key=request_key).select_related('submission').first()
    if previous:
        if previous.payload_digest!=digest:raise PermissionDenied('Request key reused with different inputs.')
        return previous.submission,False
    cp=get_object_or_404(ContestProblem,contest=c,problem__code=code)
    a=get_object_or_404(ContestVersionAdmission,contest_problem=cp,revoked=False)
    from .publication import verify_native
    from .admission import verify_approval
    try:verify_native(a.version);verify_approval(a)
    except Exception:raise PermissionDenied('Version approval is stale.') from None
    if a.runtime_id!=language or not cp.problem.allowed_languages.filter(pk=language).exists():raise PermissionDenied('Language is not enabled.')
    if not source or len(source.encode())>65536:raise PermissionDenied('Source must be 1–65536 bytes.')
    if not user.has_perm('judge.spam_submission'):
        if (Submission.objects.filter(user=user.profile).exclude(status__in=('D','IE','CE','AB')).count()>=settings.DMOJ_SUBMISSION_LIMIT or
            Submission.objects.filter(user=user.profile,date__gte=server_now()-settings.DMOJ_SUBMISSION_RATELIMIT_TIMEFRAME).exclude(status__in=('IE','CE')).count()>=settings.DMOJ_SUBMISSION_RATELIMIT):
            raise PermissionDenied('Submission limit reached.')
    receipt=server_now()
    if not c.start_time<=receipt<c.end_time:raise PermissionDenied('Official submissions require start <= server receipt < end.')
    s=Submission.objects.create(user=user.profile,problem=cp.problem,language_id=language,contest_object=c,locked_after=c.locked_after)
    Submission.objects.filter(pk=s.pk).update(date=receipt);s.date=receipt
    SubmissionSource.objects.create(submission=s,source=source)
    ContestSubmission.objects.create(submission=s,problem=cp,participation=entry.participation)
    ContestReceipt.objects.create(submission=s,entry=entry,approval=a,request_key=request_key,payload_digest=digest,
        version_digest=a.version_digest,receipt=receipt,generation=identity.generation)
    transaction.on_commit(lambda:dispatch(s.pk))
    return s,True


def dispatch(pk):
    Submission.objects.get(pk=pk).judge(force_judge=True)


def validate_receipt(s):
    r=ContestReceipt.objects.select_related('entry__contest','approval__version','approval__contest_problem').get(submission=s)
    c=r.entry.contest;a=r.approval
    from .admission import verify_approval
    from .publication import verify_native
    verify_native(a.version);verify_approval(a)
    if (s.user.user_id!=r.entry.user_id or s.contest_object_id!=c.pk or
        a.contest_problem.contest_id!=c.pk or s.problem_id!=a.version.problem_id or s.language_id!=a.runtime_id or
        r.version_digest!=a.version_digest or s.date!=r.receipt or not c.start_time<=r.receipt<c.end_time or
        r.payload_digest!=payload(s.problem.code,s.language_id,s.source.source) or
        not ContestSubmission.objects.filter(submission=s,participation_id=r.entry.participation_id,problem=a.contest_problem).exists()):
        raise PermissionDenied('Invalid durable contest receipt.')
    # No current access check: accepted jobs survive removal/end/session changes.
    return a


def scoped_submit(request,contest,problem):
    from judge.views.problem import ProblemSubmit
    c=get_object_or_404(Contest,key=contest,workflow__isnull=False)
    from .native import contest_access
    if not contest_access(request.user,c):raise Http404
    if request.method=='GET' and not content(request.user,c,submit=True):raise PermissionDenied
    class ManagedSubmit(ProblemSubmit):
        template_name='cpjudge/contest_submit.html'
        def get_context_data(self,**kwargs):
            context=super().get_context_data(**kwargs);context['request_key']=str(uuid.uuid4());context['managed_contest']=c
            return context
        def form_valid(self,form):
            from .sessions import GENERATION_KEY
            s,_=admit(request.user,c.key,problem,form.cleaned_data['language'].pk,form.cleaned_data['source'],request.POST.get('request_key'),
                generation=request.session.get(GENERATION_KEY),auth_hash=request.session.get('_auth_user_hash'))
            return redirect('submission_status',submission=s.pk)
    return ManagedSubmit.as_view()(request,problem=problem)


def rankings(request,contest):
    c=get_object_or_404(Contest,key=contest,workflow__isnull=False)
    from .native import contest_access
    if not contest_access(request.user,c) or server_now()<c.start_time:raise Http404
    from judge.views.contests import get_contest_ranking_list
    users,problems=get_contest_ranking_list(request,c,show_current_virtual=False)
    from markupsafe import Markup,escape
    removed=set(c.registrations.filter(status='removed').values_list('participation_id',flat=True))
    users=[(rank,row._replace(display_name=Markup(str(escape(row.display_name))+' (Removed)')) if row.participation.pk in removed else row) for rank,row in users]
    dq=c.registrations.filter(status='dq').select_related('user','participation')
    return render(request,'cpjudge/entry_ranking.html',dict(title='Standings: '+c.name,contest=c,users=users,problems=problems,dq=dq,has_rating=False))


def install_native():
    from judge.views import contests
    original=contests.contest_ranking_list
    def ranking_list(c,problems):
        if not hasattr(c,'workflow'):return original(c,problems)
        return contests.base_contest_ranking_list(c,problems,c.users.filter(virtual=0,is_disqualified=False,registration__status__in=('active','removed')).prefetch_related('user__organizations').order_by('-score','cumtime','id'))
    # Native get_contest_ranking_list has a default argument bound at definition.
    contests.contest_ranking_list=ranking_list
    original_get=contests.get_contest_ranking_list
    def get(request,c,*args,**kwargs):
        if hasattr(c,'workflow'):kwargs['ranking_list']=ranking_list
        return original_get(request,c,*args,**kwargs)
    contests.get_contest_ranking_list=get
    original_recompute=ContestParticipation.recompute_results
    def recompute(p):
        if hasattr(p.contest,'workflow'):return p.contest.format.update_participation(p)
        return original_recompute(p)
    ContestParticipation.recompute_results=recompute


def native_join(request,contest):
    c=get_object_or_404(Contest,key=contest)
    if c.ended:
        return HttpResponse('Virtual participation is disabled.',status=403)
    if hasattr(c,'workflow'):return register_view(request,contest)
    from judge.views.contests import ContestJoin
    return ContestJoin.as_view()(request,contest=contest)


def native_leave(request,contest):
    c=get_object_or_404(Contest,key=contest)
    if hasattr(c,'workflow'):return leave_view(request,contest)
    from judge.views.contests import ContestLeave
    return ContestLeave.as_view()(request,contest=contest)


def native_rankings(request,contest):
    c=get_object_or_404(Contest,key=contest)
    if hasattr(c,'workflow'):return rankings(request,contest)
    from judge.views.contests import ContestRanking
    return ContestRanking.as_view()(request,contest=contest)


def my_submissions(request, contest):
    """Native paginated list, bound to the signed-in account and this contest."""
    from .native import contest_access
    from judge.views.submission import UserAllContestSubmissions
    c = get_object_or_404(Contest, key=contest)
    if not contest_access(request.user, c):
        raise Http404
    if hasattr(c, 'workflow') and server_now() < c.start_time:
        raise Http404
    class OwnContestSubmissions(UserAllContestSubmissions):
        def get_queryset(self):
            return super().get_queryset().filter(contest_object=c)
    return OwnContestSubmissions.as_view()(request, contest=contest, user=request.user.username)


def native_ranking_ajax(request,contest):
    c=get_object_or_404(Contest,key=contest)
    if hasattr(c,'workflow'):return rankings(request,contest)
    from judge.views.contests import contest_ranking_ajax
    return contest_ranking_ajax(request,contest=contest)
