"""Reuse native admin shell with narrowly scoped native model forms."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .models import Identity, Audit, Grant
from .policy import allowed, CAPABILITIES

class ScopedContestAdmin(admin.ModelAdmin):
    list_display=('key','name','start_time','end_time')
    fields=('key','name','description','start_time','end_time')
    actions=None
    search_fields=('key','name')
    def has_module_permission(self,request):
        return self.has_view_permission(request)
    def has_add_permission(self,request):
        return Identity.objects.filter(user=request.user,is_author=True).exists()
    def has_view_permission(self,request,obj=None):
        if obj is not None:
            return allowed(request.user,obj,'settings.edit')
        return Grant.objects.filter(user=request.user,capability='settings.edit',revoked=False).exists() or self.has_add_permission(request)
    has_change_permission=has_view_permission
    def has_delete_permission(self,request,obj=None):
        return False
    def get_queryset(self,request):
        return super().get_queryset(request).filter(pk__in=Grant.objects.filter(user=request.user,capability='settings.edit',revoked=False).values('contest_id'))
    def get_readonly_fields(self,request,obj=None):
        # This checkpoint does not introduce post-start contest changes.
        return self.fields if obj and (hasattr(obj,'workflow') or obj.start_time<=timezone.now()) else (('key',) if obj else ())
    def save_model(self,request,obj,form,change):
        if change and hasattr(obj,'workflow'):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied('Use the scoped contest page.')
        if change and not allowed(request.user,obj,'settings.edit'):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        if not change:
            obj.is_private=True;obj.is_visible=False;obj.is_rated=False
            obj.format_name='cpjudge_icpc_v1'
        super().save_model(request,obj,form,change)
        if not change:
            from .policy import grant_scope
            for cap in CAPABILITIES:
                grant_scope(request.user,request.user,obj,cap,owner_creation=True)
        Audit.objects.create(actor=request.user,action='contest.edit' if change else 'contest.create',scope=str(obj.pk))

class AccountAdmin(admin.ModelAdmin):
    list_display=('username','first_name','last_name','is_active')
    fields=('username','first_name','last_name','email','is_active')
    readonly_fields=('username','email')
    actions=None
    search_fields=('username',)
    def has_module_permission(self,request):
        return request.user.is_superuser
    def has_view_permission(self,request,obj=None):
        return request.user.is_superuser
    has_change_permission=has_view_permission
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
    def save_model(self,request,obj,form,change):
        with transaction.atomic():
            previous=get_user_model().objects.select_for_update().get(pk=obj.pk)
            if previous.is_active!=obj.is_active:
                identity,_=Identity.objects.get_or_create(user=obj)
                identity.generation+=1;identity.save(update_fields=['generation'])
            super().save_model(request,obj,form,change)
            Audit.objects.create(actor=request.user,subject=obj,action='account.edit')


def install_admin():
    from judge.models import Contest
    # Keep registrations but hide all unsupported/global content ModelAdmins.
    # URL gate denies their direct paths too; model permissions alone are not relied on.
    for model,model_admin in list(admin.site._registry.items()):
        model_admin.has_module_permission=lambda request:False
    for model,klass in ((Contest,ScopedContestAdmin),(get_user_model(),AccountAdmin)):
        admin.site.unregister(model)
        admin.site.register(model,klass)
    admin.site.has_permission=lambda request: request.user.is_active and (
        request.user.is_superuser or Identity.objects.filter(user=request.user,is_author=True).exists() or Grant.objects.filter(user=request.user,capability='settings.edit',revoked=False).exists())
