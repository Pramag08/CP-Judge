"""Native route/model integration. Unlisted management surfaces fail closed."""
import re
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from .models import Grant, Identity, ContestEntry
from .policy import allowed


def scope_ids(user, capability):
    if not user.is_authenticated or not user.is_active:
        return []
    return Grant.objects.filter(user=user,capability=capability,revoked=False).values_list('contest_id',flat=True)


def contest_access(user, contest):
    if not user.is_authenticated or not user.is_active:
        return False
    if hasattr(contest,'workflow'):
        from .entries import restricted
        if restricted(user,contest):return False
    if contest.banned_users.filter(user=user).exists():
        return False
    if Grant.objects.filter(user=user,contest=contest,revoked=False).exists():
        return True
    if not contest.is_visible or contest.is_organization_private:
        return False
    if hasattr(contest,'workflow'):
        from .contest_manage import eligible
        return eligible(user,contest)
    return not contest.is_private or contest.private_contestants.filter(user=user).exists()


def problem_access(user, problem):
    if not user.is_authenticated or not user.is_active:
        return False
    if problem.code.startswith('pv9'):
        from .publication import published_access
        from .admission import participant_approval
        from .author_tests import authorize
        from judge.models import Contest
        for c in Contest.objects.filter(workflow__isnull=False,problems=problem):
            try:authorize(user,c);return True
            except PermissionDenied:pass
        return published_access(user,problem) or bool(participant_approval(user,problem))
    # Existing explicit native problem tester/editor memberships are preserved,
    # not inferred from account administration/global permission flags.
    if problem.testers.filter(user=user).exists() or problem.authors.filter(user=user).exists() or problem.curators.filter(user=user).exists():
        return True
    if problem.is_public and not problem.is_organization_private:
        return True
    from judge.models import Contest
    for contest in Contest.objects.filter(problems=problem):
        if hasattr(contest,'workflow'):
            from .entries import content
            if content(user,contest):return True
            continue
        if contest_access(user,contest) and (contest.start_time<=timezone.now() or
            Grant.objects.filter(user=user,contest=contest,revoked=False).exists()):
            return True
    return False


def review(user, submission, source=False):
    if not user.is_authenticated or not user.is_active:
        return False
    if hasattr(submission,'private_probe') or hasattr(submission,'author_test'): return False
    contest=submission.contest_object
    if contest and not contest_access(user,contest):
        return False
    if submission.user.user_id==user.pk:
        return problem_access(user,submission.problem)
    return bool(contest and allowed(user,contest,'source.review' if source else 'submissions.review'))


def visible_submissions(user, queryset):
    if not user.is_authenticated:
        return queryset.none()
    from judge.models import Contest
    from .models import ContestEntry
    restricted_ids=ContestEntry.objects.filter(user=user,status__in=('removed','dq')).values('contest_id')
    banned=Contest.objects.filter(Q(banned_users__user=user)|Q(pk__in=restricted_ids)).values_list('pk',flat=True)
    return queryset.filter(private_probe__isnull=True,author_test__isnull=True).filter(Q(user__user=user)|Q(contest_object_id__in=scope_ids(user,'submissions.review'))).exclude(contest_object_id__in=banned)


# Native, authenticated participant routes still execute upstream views/templates.
PARTICIPANT = frozenset('cpj_author_test cpj_register cpj_deregister cpj_entry_sanction cpj_contest_submit cpj_my_submissions cpj_contest_list cpj_contest_create cpj_contest_edit cpj_contest_problem cpj_contest_remove cpj_contest_preview cpj_contest_publish '.split()) | frozenset('home auth_login auth_logout password_change password_change_done password_reset '
    'contest_list contest_view contest_ranking contest_ranking_ajax contest_join contest_leave '
    'problem_list problem_detail problem_submit problem_editorial language_template_ajax '
    'all_submissions all_user_submissions all_user_submissions_old chronological_submissions user_submissions '
    'contest_all_user_submissions contest_user_submissions submission_source submission_source_raw submission_status '
    'submission_testcases_query submission_single_query submission_abort user_page user_problems user_pp_ajax '
    'cpj_probes cpj_probe_run cpj_auto_probe_retry cpj_events cpj_roster cpj_export cpj_export_download cpj_import_upload cpj_import_confirm cpj_import_download cpj_import_convert cpj_statement_preview cpj_statement_asset cpj_publish cpj_version_asset cpj_profile imported_statement_asset'.split())

class NativePolicyMiddleware(MiddlewareMixin):
    def process_view(self,request,view,args,kwargs):
        from judge.models import Contest, Problem, Submission
        match=request.resolver_match
        name=match.url_name if match else None
        if request.path.startswith('/static/'):
            return None
        if request.path=='/admin/login/':
            return HttpResponseRedirect('/accounts/login/?next=/admin/')
        if not request.user.is_authenticated:
            if name in ('auth_login','password_reset'):
                return None
            if request.method in ('GET', 'HEAD') and 'text/html' in request.headers.get('Accept', '') and not (
                request.path.startswith('/cpjudge/events/') or request.path.endswith('/ajax') or
                name in ('submission_testcases_query', 'submission_single_query')
            ):
                from django.urls import reverse
                from django.utils.http import url_has_allowed_host_and_scheme
                from urllib.parse import urlencode
                target = request.get_full_path()
                if not target.startswith('/') or target.startswith('//') or not url_has_allowed_host_and_scheme(
                    target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
                ):
                    target = '/'
                return HttpResponseRedirect(reverse('auth_login') + '?' + urlencode({'next': target}))
            return HttpResponse('Please sign in.',status=401)
        if request.headers.get('Authorization'):
            return HttpResponse('Use your active browser session.',status=403)
        if request.path.startswith('/admin/'):
            # Restricted native ModelAdmins enforce per-object/queryset scope.
            if not request.user.is_superuser and not Identity.objects.filter(user=request.user,is_author=True).exists() and not Grant.objects.filter(user=request.user,capability='settings.edit',revoked=False).exists():
                raise Http404
            if request.path in ('/admin/','/admin/logout/','/admin/jsi18n/'):
                return None
            admin_match=re.fullmatch(r'/admin/(auth/user|judge/contest)/(?:(?:(\d+)/change/)|add/)?',request.path)
            if admin_match:
                if admin_match[1]=='auth/user' and not request.user.is_superuser:
                    raise Http404
                if admin_match[1]=='judge/contest' and admin_match[2]:
                    obj=Contest.objects.filter(pk=int(admin_match[2])).first()
                    if not obj or not allowed(request.user,obj,'settings.edit'):raise Http404
                return None
            # All other admin models/history/custom actions/password forms are disabled.
            raise Http404
        if name in ('problem_list','problem_editorial'):
            raise Http404
        if name not in PARTICIPANT:
            raise Http404
        if 'contest' in kwargs:
            contest=Contest.objects.filter(key=kwargs['contest']).first()
            if not contest or not contest_access(request.user,contest):
                raise Http404
        if 'problem' in kwargs:
            problem=Problem.objects.filter(code=kwargs['problem']).first()
            if not problem or not problem_access(request.user,problem):
                raise Http404
            if name=='problem_submit':
                current=request.user.profile.current_contest
                if current:
                    from .entries import conflict
                    if conflict(request.user,current.contest):
                        return HttpResponse('Use the private author test mode. Official author attempts are forbidden.',status=403)
            if name=='problem_submit' and problem.contests.filter(contest__workflow__isnull=False).exists():
                current=request.user.profile.current_contest
                if current and hasattr(current.contest,'workflow'):
                    if request.method=='GET':
                        from django.urls import reverse
                        return HttpResponseRedirect(reverse('cpj_contest_submit',kwargs={'contest':current.contest.key,'problem':problem.code}))
                    return HttpResponse('Use the contest-scoped submission form.',status=403)
                if current is None or not current.contest.contest_problems.filter(problem=problem).exists():
                    return HttpResponse('An explicit contest submission is required.',status=403)
            if name=='problem_submit' and problem.code.startswith('pv9'):
                from .admission import participant_approval
                if not participant_approval(request.user,problem,submit=True):
                    return HttpResponse('A verified private contest admission and current official entry are required.',status=403)
        subid=kwargs.get('submission')
        if name in ('submission_testcases_query','submission_single_query'):
            subid=request.GET.get('id')
        if subid is not None:
            try:
                submission=Submission.objects.select_related('problem','user','contest_object').get(pk=int(subid))
            except (ValueError,TypeError,Submission.DoesNotExist):
                raise Http404
            if not review(request.user,submission,source=name in ('submission_source','submission_source_raw','problem_submit')):
                raise Http404
            if name=='submission_abort' and submission.user.user_id!=request.user.pk:
                raise Http404
        return None


def install():
    """Apply narrow method adapters at startup in web AND native task processes."""
    from judge.models import Contest, Problem, Submission
    from judge.views.submission import SubmissionsListBase
    if getattr(Contest,'_cpj_scoped',False):
        return
    Contest._cpj_scoped=True
    # Native avatars otherwise disclose a reusable MD5 of personal email on
    # other users' profile pages and send it to a third party. Use one inert icon.
    from judge.jinja2 import gravatar,registry
    def private_avatar(*args,**kwargs):
        return 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
    gravatar.gravatar=private_avatar
    registry.globals['gravatar']=private_avatar
    from django.template import engines
    for backend in engines.all():
        if hasattr(backend,'env'):backend.env.globals['gravatar']=private_avatar
    from judge import event_poster
    import time
    event_poster.last=lambda:int(time.time()*1000)
    event_poster.real=False
    from .models import Conflict
    original_live=Contest.is_live_joinable_by
    Contest.is_live_joinable_by=lambda obj,user: not (user.is_authenticated and Conflict.objects.filter(user=user,contest=obj).exists()) and original_live(obj,user)
    original_spectate=Contest.is_spectatable_by
    Contest.is_spectatable_by=lambda obj,user: contest_access(user,obj) and original_spectate(obj,user)
    Contest.is_editable_by=lambda obj,user: allowed(user,obj,'settings.edit')
    original_access=Contest.access_check
    def access(obj,user):
        if not contest_access(user,obj):
            raise obj.Inaccessible()
        # Explicit scoped grant can read drafts without broad global permissions.
        if Grant.objects.filter(user=user,contest=obj,revoked=False).exists():
            return
        if hasattr(obj,'workflow'):return
        return original_access(obj,user)
    Contest.access_check=access
    original_labels=Contest.get_label_for_problem.func
    def labels(obj):
        if not hasattr(obj,'workflow'):return original_labels(obj)
        values=list(obj.contest_problems.order_by('order','pk').values_list('workflow_label__label',flat=True))
        return lambda index:values[index] if 0<=index<len(values) else str(index+1)
    from django.utils.functional import cached_property
    Contest.get_label_for_problem=cached_property(labels)
    Contest.get_label_for_problem.__set_name__(Contest,'get_label_for_problem')
    original_visible=Contest.get_visible_contests.__func__
    def visible(cls,user):
        qs=cls.objects.all()
        if not user.is_authenticated:
            return qs.none()
        return qs.filter(Q(pk__in=Grant.objects.filter(user=user,revoked=False).values('contest_id'))|
            (Q(is_visible=True,is_organization_private=False)&(Q(is_private=False)|Q(private_contestants__user=user)|Q(workflow__isnull=False)))).exclude(banned_users__user=user).exclude(pk__in=ContestEntry.objects.filter(user=user,status__in=('removed','dq')).values('contest_id')).distinct()
    Contest.get_visible_contests=classmethod(visible)
    def visible_problems(cls,user):
        if not user.is_authenticated:return cls.objects.none()
        eligible=Contest.get_visible_contests(user).filter(Q(start_time__lte=timezone.now())|
            Q(pk__in=Grant.objects.filter(user=user,revoked=False).values('contest_id')))
        from .admission import participant_approval
        released=[p.pk for p in cls.objects.filter(code__startswith='pv9') if participant_approval(user,p)]
        return cls.objects.filter(Q(is_public=True,is_organization_private=False)|Q(testers__user=user)|
            Q(authors__user=user)|Q(curators__user=user)|Q(contests__contest_id__in=eligible.values('pk'))).exclude(Q(code__startswith='pv9')&~Q(pk__in=released)).distinct()
    Problem.get_visible_problems=classmethod(visible_problems)
    from judge.views import submission as submission_views
    def filter_visible(queryset,user):
        # Native helper mutates its queryset. Keep that contract using bound ORM
        # parameters instead of upstream's str(QuerySet.query) SQL interpolation.
        queryset.query.add_q(Q(problem_id__in=Problem.get_visible_problems(user).values('pk')))
    submission_views.filter_submissions_by_visible_problems=filter_visible
    original_group=submission_views.group_test_cases
    def private_cases(cases):
        safe=list(cases)
        for case in safe:
            case.output='';case.feedback='';case.extended_feedback=''
        return original_group(safe)
    submission_views.group_test_cases=private_cases
    Problem.is_accessible_by=lambda obj,user,skip_contest_problem_check=False:problem_access(user,obj)
    # Website hidden-package modification/download stays disabled pending import gates.
    Problem.is_editable_by=lambda obj,user:False
    from django.db import transaction, connection
    original_judge=Submission.judge
    def judge_after_commit(obj,*args,**kwargs):
        if obj.contest_object_id and not hasattr(obj,'admission_receipt'):
            from .entries import conflict
            if conflict(obj.user.user,obj.contest_object):raise PermissionDenied('Conflicted author attempt.')
        if obj.problem.code.startswith('pv9'):
            from .admission import validate_execution
            try:validate_execution(obj)
            except Exception:
                if connection.in_atomic_block:transaction.set_rollback(True)
                raise PermissionDenied('A verified private contest receipt is required.') from None
        if connection.in_atomic_block:
            transaction.on_commit(lambda:original_judge(obj,*args,**kwargs))
            return
        return original_judge(obj,*args,**kwargs)
    judge_after_commit.alters_data=True
    Submission.judge=judge_after_commit
    Submission.can_see_detail=lambda obj,user:review(user,obj) or review(user,obj,source=True)
    original_qs=SubmissionsListBase._get_queryset
    def scoped_qs(obj):
        return visible_submissions(obj.request.user,original_qs(obj))
    SubmissionsListBase._get_queryset=scoped_qs
    # Never use the native global statistics cache to disclose unrelated attempts.
    from judge.views.submission import AllSubmissions
    AllSubmissions._get_result_data=SubmissionsListBase._get_result_data
    from .entries import install_native
    install_native()
    from .admin import install_admin
    install_admin()
    from .tasks import guard_native_tasks
    guard_native_tasks()
