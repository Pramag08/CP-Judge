"""Serialize authentication generations, including request admission, on User rows."""
import re
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import transaction
from django.dispatch import receiver
from django.http import HttpResponse
from django.shortcuts import redirect
from .models import Identity

GENERATION_KEY = 'cpjudge_generation'


@receiver(user_logged_in, dispatch_uid='cpjudge.login_generation')
def logged_in(sender, request, user, **kwargs):
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=user.pk)
        identity, _ = Identity.objects.get_or_create(user=user)
        identity.generation += 1
        identity.save(update_fields=['generation'])
        request.session[GENERATION_KEY] = identity.generation


@receiver(user_logged_out, dispatch_uid='cpjudge.logout_generation')
def logged_out(sender, request, user, **kwargs):
    if user is None or request is None:
        return
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=user.pk)
        identity = Identity.objects.filter(user=user).first()
        if identity and request.session.get(GENERATION_KEY) == identity.generation:
            identity.generation += 1
            identity.save(update_fields=['generation'])


class GenerationMiddleware:
    """Hold the account lock through view admission; do not rely on cached sessions.

    Install immediately after AuthenticationMiddleware. Streaming event endpoints
    require separate per-message authorization and are not admitted by this class.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
            identity, _ = Identity.objects.get_or_create(user=user)
            valid = (user.is_active and request.session.get(GENERATION_KEY) == identity.generation
                     and request.session.get('_auth_user_hash') == user.get_session_auth_hash())
            if not valid:
                # Drop stale identity without revoking the replacement generation.
                request.session.flush()
                from django.contrib.auth.models import AnonymousUser
                request.user = AnonymousUser()
                return HttpResponse('This session was replaced. Please sign in again.', status=401)
            request.user = user
            request.cpj_identity = identity
            # C10 needs separately committed DB/FS phases. Only this POST
            # releases the admission transaction; its service rechecks the same
            # session generation/hash and scope under each account lock.
            publication = request.method == 'POST' and re.fullmatch(r'/imports/[0-9]+/publish/',request.path_info)
            # D11 must lock actor and target accounts in sorted order before
            # the contest (including the audit subject FK). Its service rechecks
            # this same session generation/hash under those locks.
            sanction = request.method == 'POST' and re.fullmatch(r'/contest/[a-z0-9]+/entries/[0-9]+/sanction',request.path_info)
            if not publication and not sanction:
                response = self.get_response(request)
                response['Cache-Control'] = 'private, no-store'
                return response
        response = self.get_response(request)
        response['Cache-Control'] = 'private, no-store'
        return response
