"""Explicit contest capabilities; account administration is not a content grant."""
from django.core.exceptions import PermissionDenied
from .models import Grant

CAPABILITIES = frozenset({'settings.edit','problems.import','problems.publish','roster.read',
    'roster.export','entrants.manage','submissions.review','source.review','clarifications.edit','grants.manage'})


def allowed(user, contest, capability):
    return user.is_authenticated and user.is_active and capability in CAPABILITIES and Grant.objects.filter(
        user=user, contest=contest, capability=capability, revoked=False).exists()


def require(user, contest, capability):
    if not allowed(user, contest, capability):
        raise PermissionDenied


def roster(user, contest, *, export=False):
    require(user, contest, 'roster.export' if export else 'roster.read')
    # Scoped query, same authorization for UI and export; email never in standings.
    from django.db.models.functions import Coalesce
    return contest.users.select_related('user__user').annotate(college_id=Coalesce('user__user__identity__college_id','user__user__username')).values('college_id',
        'user__user__first_name', 'user__user__last_name', 'user__user__email')


def grant_scope(actor, user, contest, capability, *, revoke=False, owner_creation=False):
    from django.contrib.auth import get_user_model
    from django.db import transaction
    from judge.models import ContestParticipation
    from .models import Audit, Conflict
    if capability not in CAPABILITIES:
        raise PermissionDenied
    with transaction.atomic():
        # Same lock as request/background admission and generation replacement.
        get_user_model().objects.select_for_update().get(pk=user.pk)
        if not (owner_creation and actor.pk==user.pk) and not actor.is_superuser:
            require(actor,contest,'grants.manage')
            require(actor,contest,capability)
        from judge.models import Contest
        Contest.objects.select_for_update().get(pk=contest.pk)
        grant,_=Grant.objects.update_or_create(user=user,contest=contest,capability=capability,
                    defaults={'grantor':actor,'revoked':revoke})
        if not revoke and capability not in ('roster.read','roster.export'):
            Conflict.objects.get_or_create(user=user,contest=contest)
            # Preserve native attempts and mark current/future scope participation unranked.
            ContestParticipation.objects.filter(user__user=user,contest=contest,virtual=0).update(virtual=-1)
        if hasattr(contest,'workflow'):
            from .entries import update_count
            update_count(contest)
        Audit.objects.create(actor=actor,subject=user,action='grant.revoke' if revoke else 'grant.create',
                             scope=str(contest.pk)+':'+capability)
        return grant
