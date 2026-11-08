import hashlib
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django import forms

class EmailAuthenticationForm(AuthenticationForm):
    username=forms.CharField(label='Personal email (legacy ID available while migration is pending)',max_length=254)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['username'].max_length=254
        self.fields['username'].widget.attrs.update({'maxlength':254,'autocomplete':'username','placeholder':'Personal email'})
        from .email_identity import email_only
        if email_only():self.fields['username'].label='Personal email'
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse
from .identity import canonical_id
from .models import Identity, Audit
from .sessions import GENERATION_KEY


class LocalLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = EmailAuthenticationForm
    extra_context = {'title':'Personal email login'}
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        # Counters use the configured shared Redis cache; no password in keys.
        cid = request.POST.get('username', '').strip().lower()
        keys = ['cpj:login:' + hashlib.sha256(value.encode()).hexdigest() for value in (
            'id:' + cid, 'ip:' + request.META.get('REMOTE_ADDR',''))]
        for key in keys:
            cache.add(key, 0, timeout=300)
            if cache.incr(key) > 30:
                return HttpResponse('Too many attempts. Try again in five minutes.', status=429)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # Authenticate again under the same lock as reset/disable. A credential
        # checked before a concurrent reset cannot create a valid new session.
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=form.get_user().pk)
            from .identity import CollegeBackend
            authenticated=CollegeBackend().authenticate(self.request,username=form.cleaned_data['username'],password=form.cleaned_data['password'])
            if authenticated is None or authenticated.pk != user.pk:
                form.add_error(None, 'Credentials changed. Please sign in again.')
                return self.form_invalid(form)
            response = super().form_valid(form)
            return response


class LocalPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_form.html'

    def form_valid(self, form):
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=self.request.user.pk)
            response = super().form_valid(form)
            identity = Identity.objects.get(user=self.request.user)
            identity.generation += 1
            identity.must_change_password = False
            identity.save(update_fields=['generation','must_change_password'])
            self.request.session[GENERATION_KEY] = identity.generation
            Audit.objects.create(actor=self.request.user, subject=self.request.user, action='password.change')
            return response


def recovery(request):
    return HttpResponse('Contact the organizers outside this application for recovery. An authorized account administrator verifies the requester and resets the password. No reset email or token is sent.')


def events(request, channels):
    """Short authenticated polls; every poll rechecks generation and current scope."""
    import hmac, re, time
    from django.http import Http404, JsonResponse
    from judge.models import Submission, Contest
    from .native import review, visible_submissions, contest_access
    messages=[]
    parts=channels.split('|')
    if len(parts)>4:
        raise Http404
    for channel in parts:
        if channel.startswith('sub_') and re.fullmatch(r'sub_[a-f0-9]{24}',channel):
            sid=int(channel[-8:],16)
            sub=Submission.objects.select_related('user','problem','contest_object').filter(pk=sid).first()
            if not sub or not hmac.compare_digest(channel[4:],sub.id_secret) or not review(request.user,sub):
                raise Http404
            messages.append({'type':'grading-end' if sub.is_graded else 'test-case'})
        elif channel=='submissions':
            for sub in visible_submissions(request.user,Submission.objects.all()).order_by('-id')[:20]:
                messages.append({'type':'done-submission' if sub.is_graded else 'update-submission',
                    'state':'test-case','id':sub.pk,'user':sub.user_id,'problem':sub.problem_id,'contest':sub.contest_object_id})
        elif re.fullmatch(r'contest_\d+',channel):
            contest=Contest.objects.filter(pk=int(channel[8:])).first()
            if not contest or not contest_access(request.user,contest):raise Http404
            messages.append({'type':'update'})
        else:
            raise Http404
    response=JsonResponse({'id':int(time.time()*1000),'messages':messages})
    response['Cache-Control']='private, no-store'
    return response


def roster_view(request, contest):
    from django.shortcuts import get_object_or_404, render
    from judge.models import Contest
    from .policy import roster
    obj=get_object_or_404(Contest,key=contest)
    if hasattr(obj,'workflow'):
        from .entries import roster as entry_roster
        return entry_roster(request,obj)
    rows=list(roster(request.user,obj))
    return render(request,'cpjudge/roster.html',{'title':'Contest roster','contest':obj,'rows':rows})


def roster_export(request,contest):
    from django.http import Http404
    from judge.models import Contest
    if Contest.objects.filter(key=contest,workflow__isnull=False).exists():raise Http404
    from django.shortcuts import get_object_or_404, redirect
    from django.views.decorators.csrf import csrf_protect
    from judge.models import Contest
    from .policy import require
    from .models import ExportJob
    from .tasks import export_roster
    import secrets
    if request.method!='POST':return HttpResponse(status=405)
    obj=get_object_or_404(Contest,key=contest)
    require(request.user,obj,'roster.export')
    job=ExportJob.objects.create(owner=request.user,contest=obj,generation=request.cpj_identity.generation,token=secrets.token_hex(24))
    transaction.on_commit(lambda:export_roster.delay(job.pk))
    return redirect('cpj_export_download',token=job.token)


def export_download(request, token):
    from django.http import Http404
    from .models import ExportJob
    from .tasks import export_authorized, EXPORT_ROOT
    job=ExportJob.objects.select_related('contest').filter(owner=request.user,token=token).first()
    if not job:raise Http404
    export_authorized(job)
    if job.status!='ready':return HttpResponse('Export queued. Refresh this page.',status=202)
    response=HttpResponse((EXPORT_ROOT/(job.token+'.csv')).read_bytes(),content_type='text/csv; charset=utf-8')
    response['Content-Disposition']='attachment; filename="contest-roster.csv"'
    response['X-Content-Type-Options']='nosniff'
    return response


def own_profile(request):
    from django import forms
    from django.shortcuts import render, redirect
    class ContactForm(forms.ModelForm):
        class Meta:
            model=get_user_model()
            fields=('first_name','last_name')
    form=ContactForm(request.POST or None,instance=request.user)
    if request.method=='POST' and form.is_valid():
        form.save()
        Audit.objects.create(actor=request.user,subject=request.user,action='profile.edit')
        return redirect('cpj_profile')
    return render(request,'cpjudge/profile.html',{'title':'My profile','form':form,'college_id':request.cpj_identity.college_id,'email':request.user.email})


def import_upload(request, contest):
    """Accept one private ZIP and queue its bounded conversion."""
    from django.core.exceptions import PermissionDenied, RequestDataTooBig, ValidationError
    from django.http import Http404
    from django.shortcuts import get_object_or_404, redirect, render
    from django.http.multipartparser import MultiPartParserError
    from judge.models import Contest
    from .imports import archive_limits, upload
    from .uploads import BoundedZipUploadHandler

    obj=get_object_or_404(Contest,key=contest)
    from .imports import authorize
    try:
        authorize(request.user,obj)
    except PermissionDenied:
        raise Http404
    maximum=archive_limits().upload_bytes
    maximum_label=f'{maximum/(1024**2):g} MiB'
    title='Import ZIP'
    if request.method=='GET':
        return render(request,'cpjudge/import_upload.html',{'title':title,'contest':obj,'maximum_label':maximum_label})

    def error(message,status=400):
        return render(request,'cpjudge/import_upload.html',{
            'title':title,'contest':obj,'maximum_label':maximum_label,'error':message},status=status)
    if not (request.content_type or '').startswith('multipart/form-data'):
        return error('Choose one ZIP file using the upload form.')
    try:
        files=[item for key in request.FILES for item in request.FILES.getlist(key)]
    except (RequestDataTooBig,MultiPartParserError):
        return error('The request is too large or is not a valid multipart upload.',413)
    boundary=getattr(request,'cpj_zip_upload_handler',None)
    if isinstance(boundary,BoundedZipUploadHandler):
        if boundary.exceeded:
            return error('The ZIP exceeds the configured upload limit.',413)
        if boundary.multiple:
            return error('Upload exactly one ZIP file per request.')
    if len(files)>1:
        return error('Upload exactly one ZIP file per request.')
    if len(files)!=1:
        return error('Choose one ZIP file before submitting.')
    try:
        job=upload(request.user,files[0],obj,validate_archive=True)
    except ValidationError as exc:
        message=' '.join(exc.messages)
        return error(message)
    except ValueError as exc:
        # ArchiveRejected is a ValueError from the strict bounded ZIP preflight.
        return error(str(exc))
    except OSError:
        return error('The ZIP could not be stored. Please contact the administrator.',503)
    from .conversion import queue_conversion
    queue_conversion(request.user,job.pk)
    return redirect('cpj_import_confirm',job_id=job.pk)


def import_confirm(request, job_id):
    from django.shortcuts import render
    from zoneinfo import ZoneInfo
    from .imports import owned
    from .conversion import reconcile_imports
    owned(request.user,job_id)
    reconcile_imports(job_id=job_id)
    job=owned(request.user,job_id)
    from .compatibility import preview,public_error
    from .models import ProblemVersion
    from .policy import allowed
    version=ProblemVersion.objects.filter(job=job,attempt=job.attempt).first()
    check_status,check_message=(None,None)
    if version and version.state=='published':
        from .auto_probe import status
        check_status,check_message=status(version)
    can_publish=bool(job.contest_id and allowed(request.user,job.contest,'problems.publish'))
    ready_to_add=False
    if check_status=='Ready' and can_publish:
        try:
            from .publication import verify_native
            from .probes import binding
            from .models import ProblemProbe
            from .contest_readiness import check
            probe=ProblemProbe.objects.filter(version=version,solution__name='Automatic reference check').select_related('solution__runtime').order_by('-pk').first()
            binding(probe)
            verify_native(version)
            check(version.code,probe.solution.runtime.key)
            ready_to_add=True
        except Exception:
            check_status,check_message='Checking problem','The published version or compatible judge is not ready. Refresh after checking the worker.'
    problems=list(job.contest.contest_problems.select_related('workflow_label').all()) if job.contest_id else []
    already_added=bool(version and any(p.problem_id==version.problem_id for p in problems))
    used={p.workflow_label.label for p in problems}
    next_label=next((x for x in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if x not in used),'A')
    next_order=max((p.order for p in problems),default=-1)+1
    zone=ZoneInfo(job.contest.workflow.display_timezone) if job.contest_id and hasattr(job.contest,'workflow') else ZoneInfo('UTC')
    transient=job.error in {'The conversion queue is unavailable. Please retry.', 'Conversion service busy. Please retry.', 'Conversion was interrupted or did not start before its deadline. Please retry.', 'Conversion exceeded a resource limit or stopped unexpectedly. Review package size and retry.'}
    response=render(request,'cpjudge/import_confirm.html',{'version':version,'can_publish':can_publish,'title':'Import ZIP','job':job,'preview':preview(job),'public_error':public_error(job),'check_status':check_status,'check_message':check_message,'ready_to_add':ready_to_add,'already_added':already_added,'next_label':next_label,'next_order':next_order,'zone':zone,'transient':transient})
    response['Cache-Control']='private, no-store'
    return response


def import_convert(request,job_id):
    if request.method!='POST':return HttpResponse(status=405)
    from django.shortcuts import redirect
    from .conversion import queue_conversion,reconcile_imports
    from .imports import owned
    owned(request.user,job_id)
    reconcile_imports(job_id=job_id)
    queue_conversion(request.user,job_id)
    return redirect('cpj_import_confirm',job_id=job_id)


def import_download(request, job_id):
    from django.http import FileResponse, Http404
    from .imports import owned, private_root
    job=owned(request.user,job_id)
    root=private_root()
    path=(root/job.archive_key).resolve()
    if path.parent!=root or not path.is_file():
        raise Http404
    response=FileResponse(path.open('rb'),content_type='application/zip',as_attachment=True,
                          filename='uploaded-package.zip')
    response['Cache-Control']='private, no-store'
    response['X-Content-Type-Options']='nosniff'
    return response
