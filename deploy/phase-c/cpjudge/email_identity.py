"""Private canonical keys, explicit corrections, and conflict-blocked cutover."""
import secrets
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from .identity import require_admin
from .models import Identity, Audit, EmailLoginPolicy


def canonical_email(value):
    value=value.strip().lower()
    if not value.isascii() or len(value)>254:
        raise ValidationError('Use a valid ASCII email address of at most 254 characters.')
    validate_email(value)
    return value


def lock_policy():
    EmailLoginPolicy.objects.get_or_create(pk=1)
    return EmailLoginPolicy.objects.select_for_update().get(pk=1)


def email_only():
    return EmailLoginPolicy.objects.filter(pk=1,email_only=True).exists()


def inventory():
    groups=defaultdict(list);issues=[]
    for user in get_user_model().objects.order_by('pk'):
        try:key=canonical_email(user.email)
        except ValidationError:
            issues.append({'user_id':user.pk,'issue':'missing' if not user.email.strip() else 'invalid'});continue
        groups[key].append(user.pk)
    mapping={}
    for key,ids in groups.items():
        if len(ids)>1:issues.extend({'user_id':pk,'issue':'conflict','canonical_email':key} for pk in ids)
        else:mapping[ids[0]]=key
    return mapping,issues


@transaction.atomic
def stage_keys(actor):
    require_admin(actor)
    lock_policy()
    list(get_user_model().objects.select_for_update().order_by('pk'))
    mapping,issues=inventory()
    for pk,key in mapping.items():
        identity,_=Identity.objects.get_or_create(user_id=pk)
        if identity.canonical_email not in (None,key):
            raise ValidationError('Email mapping changed. Use an audited correction.')
        identity.canonical_email=key;identity.save(update_fields=['canonical_email'])
    Audit.objects.create(actor=actor,action='email.stage',details={'mapped':len(mapping),'unresolved':len(issues)})
    return {'mapped':len(mapping),'unresolved':len(issues)}


@transaction.atomic
def set_mode(actor, enabled, reason):
    require_admin(actor)
    if not reason.strip():raise ValidationError('An audit reason is required.')
    lock_policy()
    list(get_user_model().objects.select_for_update().order_by('pk'))
    policy,_=EmailLoginPolicy.objects.get_or_create(pk=1)
    policy=EmailLoginPolicy.objects.select_for_update().get(pk=1)
    mapping,issues=inventory()
    if enabled and (issues or any(not Identity.objects.filter(user_id=pk,canonical_email=key).exists() for pk,key in mapping.items())):
        raise ValidationError('Email-only cutover blocked by unresolved or unstaged identities. Inspect the private inventory.')
    policy.email_only=enabled;policy.save(update_fields=['email_only'])
    # Cutover and operational rollback both revoke existing generations. Never
    # restore a stale DB or replay passwords; intervening data is retained.
    from django.db.models import F
    Identity.objects.update(generation=F('generation')+1)
    Audit.objects.create(actor=actor,action='email.cutover' if enabled else 'email.rollback',details={'reason':reason})


@transaction.atomic
def correct_email(actor,user_id,email,reason,*,assignment_kind=None):
    require_admin(actor)
    if not reason.strip():raise ValidationError('An audit reason is required.')
    if assignment_kind not in (None,'organizer_assigned_development'):
        raise ValidationError('Unsupported address assignment provenance.')
    key=canonical_email(email)
    lock_policy()
    user=get_user_model().objects.select_for_update().get(pk=user_id)
    identity,_=Identity.objects.get_or_create(user=user)
    identity=Identity.objects.select_for_update().get(pk=identity.pk)
    identity.canonical_email=key;identity.generation+=1
    identity.save(update_fields=['canonical_email','generation'])  # DB unique, including races.
    user.email=key;user.save(update_fields=['email'])
    details={'reason':reason}
    if assignment_kind=='organizer_assigned_development':
        details.update(address_basis=assignment_kind,development_fixture=True,mailbox_verified=False,real_participant_identity=False)
    Audit.objects.create(actor=actor,subject=user,action='email.correct',details=details)
    return user


@transaction.atomic
def provision_email(actor,email,*,first_name='',last_name='',author=False):
    require_admin(actor)
    key=canonical_email(email);password=secrets.token_urlsafe(24)
    lock_policy()
    user=get_user_model().objects.create_user(username='u'+secrets.token_hex(15),password=password,email=key,
        first_name=first_name,last_name=last_name)
    from judge.models import Profile
    Profile.objects.get_or_create(user=user)
    Identity.objects.create(user=user,canonical_email=key,must_change_password=False,is_author=author)
    Audit.objects.create(actor=actor,subject=user,action='account.provision')
    return user,password


class EmailBackend(ModelBackend):
    def authenticate(self,request,username=None,password=None,**kwargs):
        try:key=canonical_email(username or '')
        except ValidationError:key=None
        identity=Identity.objects.select_related('user').filter(canonical_email=key).first() if key else None
        if identity:
            user=identity.user
            try:current=canonical_email(user.email)==key
            except ValidationError:current=False
            if current and user.check_password(password) and self.user_can_authenticate(user):return user
        get_user_model()().set_password(password)
        return None
