from django.urls import path
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.shortcuts import redirect
from . import views, probes, entries, auto_probe, contest_manage as cm
from .statement import statement_preview,statement_asset
from .publication import publish_view,version_asset
from . import author_tests
urlpatterns=[
    path('author/contests/<str:contest_key>/test/<str:problem>/',author_tests.page,name='cpj_author_test'),
    path('',lambda request:redirect('contest_list'),name='home'),
    path('author/contests/',cm.listing,name='cpj_contest_list'),
    path('author/contests/create/',cm.create,name='cpj_contest_create'),
    path('author/contests/<str:contest_key>/',cm.edit,name='cpj_contest_edit'),
    path('author/contests/<str:contest_key>/problem/',cm.problem,name='cpj_contest_problem'),
    path('author/contests/<str:contest_key>/remove/',cm.remove,name='cpj_contest_remove'),
    path('author/contests/<str:contest_key>/preview/',cm.preview,name='cpj_contest_preview'),
    path('author/contests/<str:contest_key>/publish/',cm.publish,name='cpj_contest_publish'),
    path('contest/<str:contest>',cm.overview,name='contest_view'),
    path('contest/<str:contest>/join',entries.native_join,name='contest_join'),
    path('contest/<str:contest>/leave',entries.native_leave,name='contest_leave'),
    path('contest/<str:contest>/register',entries.register_view,name='cpj_register'),
    path('contest/<str:contest>/deregister',entries.deregister_view,name='cpj_deregister'),
    path('contest/<str:contest>/entries/<int:entry_id>/sanction',entries.sanction_view,name='cpj_entry_sanction'),
    path('contest/<str:contest>/problem/<str:problem>/submit',entries.scoped_submit,name='cpj_contest_submit'),
    path('contest/<str:contest>/ranking/',entries.native_rankings,name='contest_ranking'),
    path('contest/<str:contest>/my-submissions/',entries.my_submissions,name='cpj_my_submissions'),
    path('contest/<str:contest>/ranking/ajax',entries.native_ranking_ajax,name='contest_ranking_ajax'),
    path('private-versions/<int:version_id>/probes/',probes.page,name='cpj_probes'),
    path('private-versions/<int:version_id>/probes/run/',probes.run,name='cpj_probe_run'),
    path('private-versions/<int:version_id>/automatic-check/',auto_probe.retry_view,name='cpj_auto_probe_retry'),
    path('accounts/login/',views.LocalLoginView.as_view(),name='auth_login'),
    path('accounts/logout/',LogoutView.as_view(),name='auth_logout'),
    path('accounts/password/change/',views.LocalPasswordChangeView.as_view(),name='password_change'),
    path('accounts/password/reset/',views.recovery,name='password_reset'),
    path('admin/password_change/',views.LocalPasswordChangeView.as_view()),
    path('edit/profile/',views.own_profile,name='cpj_profile'),
    path('cpjudge/events/<path:channels>',views.events,name='cpj_events'),
    path('contest/<str:contest>/roster',views.roster_view,name='cpj_roster'),
    path('contest/<str:contest>/roster/export',views.roster_export,name='cpj_export'),
    path('contest/<str:contest>/import/',views.import_upload,name='cpj_import_upload'),
    path('imports/<int:job_id>/',views.import_confirm,name='cpj_import_confirm'),
    path('imports/<int:job_id>/statement/',statement_preview,name='cpj_statement_preview'),
    path('imports/<int:job_id>/statement/<int:attempt>/assets/<str:asset>',statement_asset,name='cpj_statement_asset'),
    path('imports/<int:job_id>/publish/',publish_view,name='cpj_publish'),
    path('problem/<str:problem>/published-assets/<str:asset>',version_asset,name='cpj_version_asset'),
    path('imports/<int:job_id>/convert/',views.import_convert,name='cpj_import_convert'),
    path('imports/<int:job_id>/download/',views.import_download,name='cpj_import_download'),
    path('cpjudge/exports/<str:token>',views.export_download,name='cpj_export_download'),
]
from dmoj.urls import urlpatterns as native_patterns
urlpatterns+=native_patterns
