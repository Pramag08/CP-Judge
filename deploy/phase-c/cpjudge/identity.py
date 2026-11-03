import re
import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, IntegrityError
from .models import Identity, Audit


def canonical_id(value):
    value = value.strip()
    # Reject Unicode before uppercase (ß must never turn into SS).
    if not value.isascii():
        raise ValidationError('College ID must use ASCII characters.')
    value = value.upper()
    pattern = getattr(settings, 'CPJ_COLLEGE_ID_PATTERN', r'[A-Z0-9][A-Z0-9_-]{0,63}')
    if not re.fullmatch(pattern, value):
        raise ValidationError('College ID does not match the configured college syntax.')
    return value


def require_admin(actor):
    if not actor.is_active or not actor.is_superuser:
        raise PermissionDenied


@transaction.atomic
def provision(actor, college_id, *, first_name='', last_name='', email='', author=False):
    require_admin(actor)
    from .email_identity import lock_policy,canonical_email
    policy=lock_policy()
    if policy.email_only and not email:raise ValidationError('Email is required after cutover.')
    cid = canonical_id(college_id)
    from .models import CollegeIDHistory
    if CollegeIDHistory.objects.filter(college_id=cid).exists():
        raise IntegrityError('College ID is reserved by an existing account.')
    # Both username and canonical ID are DB-unique. Collision rolls back everything.
    user = get_user_model().objects.create_user(username=cid, password=secrets.token_urlsafe(24),
                    first_name=first_name, last_name=last_name, email=email)
    temporary = secrets.token_urlsafe(24)
    user.set_password(temporary)
    user.save(update_fields=['password'])
    from judge.models import Profile
    Profile.objects.get_or_create(user=user)
    from .email_identity import canonical_email
    key=canonical_email(email) if email else None
    Identity.objects.create(user=user, college_id=cid, canonical_email=key,must_change_password=False, is_author=author)
    CollegeIDHistory.objects.create(college_id=cid,user=user,actor=actor,reason='Provisioned')
    Audit.objects.create(actor=actor, subject=user, action='account.provision')
    return user, temporary


@transaction.atomic
def reset_account(actor,user_id,*,reason,requester_verified):
    require_admin(actor)
    if requester_verified is not True or not reason.strip():
        raise ValidationError('The account administrator must verify the requester outside the app and record a reason.')
    from django.core.cache import cache
    key='cpj:reset:account:'+str(user_id)
    cache.add(key,0,timeout=300)
    if cache.incr(key)>10:raise ValidationError('Too many resets. Try again in five minutes.')
    user=get_user_model().objects.select_for_update().get(pk=user_id)
    identity,_=Identity.objects.get_or_create(user=user)
    identity=Identity.objects.select_for_update().get(pk=identity.pk)
    password=secrets.token_urlsafe(24)
    user.set_password(password);user.save(update_fields=['password'])
    identity.generation+=1;identity.must_change_password=False
    identity.save(update_fields=['generation','must_change_password'])
    Audit.objects.create(actor=actor,subject=user,action='account.reset',details={'reason':reason,'requester_verification':'administrator-attested-outside-app'})
    return user,password


@transaction.atomic
def reset(actor,college_id,*,reason='',requester_verified=False):
    require_admin(actor)
    identity=Identity.objects.get(college_id=canonical_id(college_id))
    return reset_account(actor,identity.user_id,reason=reason,requester_verified=requester_verified)


class CollegeBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            from .email_identity import EmailBackend,email_only
            if '@' in (username or ''):
                return EmailBackend().authenticate(request,username=username,password=password)
            if email_only():
                get_user_model()().set_password(password)
                return None
            cid = canonical_id(username or '')
        except ValidationError:
            cid = None
        identity = Identity.objects.select_related('user').filter(college_id=cid).first() if cid else None
        if identity is not None:
            user = identity.user
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        else:
            # Baseline compatibility: exact legacy username only, never email.
            user = get_user_model().objects.filter(username=username).first()
            if user and user.username == username and not Identity.objects.filter(user=user, college_id__isnull=False).exists():
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
        # Match Django's expensive nonexistent-user password path.
        get_user_model()().set_password(password)
        return None

@transaction.atomic
def correct_id(actor, user_id, college_id, reason):
    """Explicit operator correction; keep immutable User PK/history and old ID reserved."""
    from .models import CollegeIDHistory
    require_admin(actor)
    if not reason.strip():
        raise ValidationError('An audit reason is required.')
    cid = canonical_id(college_id)
    user = get_user_model().objects.select_for_update().get(pk=user_id)
    identity, _ = Identity.objects.get_or_create(user=user)
    old = identity.college_id
    if old == cid:
        return user
    # Namespace includes exact legacy usernames (case-insensitive DB uniqueness)
    # and all current/historical college IDs. Never silently merge identities.
    if (get_user_model().objects.filter(username=cid).exclude(pk=user.pk).exists()
            or Identity.objects.filter(college_id=cid).exclude(user=user).exists()
            or CollegeIDHistory.objects.filter(college_id=cid).exclude(user=user).exists()):
        raise ValidationError('College ID is already reserved; no account was changed.')
    if old:
        CollegeIDHistory.objects.get_or_create(college_id=old, defaults={'user':user,'actor':actor,'reason':reason})
    reservation, _ = CollegeIDHistory.objects.get_or_create(college_id=cid, defaults={'user':user,'actor':actor,'reason':reason})
    if reservation.user_id != user.pk:
        raise ValidationError('College ID is already reserved; no account was changed.')
    identity.college_id = cid
    identity.generation += 1
    identity.save(update_fields=['college_id','generation'])
    Audit.objects.create(actor=actor,subject=user,action='college_id.correct',scope=str(user.pk),details={'old':old,'new':cid,'reason':reason})
    return user
