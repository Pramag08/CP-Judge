"""Isolated test routes; not installed in production/live URLconf."""
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.urls import path
from .views import LocalLoginView, LocalPasswordChangeView, recovery

urlpatterns = [
    path('accounts/login/', LocalLoginView.as_view(), name='auth_login'),
    path('accounts/password/change/', LocalPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password/change/done/', lambda r:HttpResponse('Password changed'), name='password_change_done'),
    path('accounts/logout/', LogoutView.as_view(), name='auth_logout'),
    path('accounts/password/reset/', recovery, name='password_reset'),
    path('protected/', lambda r:HttpResponse(str(r.user.pk)) if r.user.is_authenticated else HttpResponse(status=401)),
]

from dmoj.urls import urlpatterns as native_patterns
urlpatterns += native_patterns
