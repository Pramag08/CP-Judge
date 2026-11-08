"""Additive policy records; native User/Profile remain authoritative account data."""
from django.conf import settings
from django.db import models

class Identity(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    # Existing baseline accounts are NOT assigned guessed college IDs.
    college_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    canonical_email = models.CharField(max_length=254,unique=True,null=True,blank=True)
    must_change_password = models.BooleanField(default=False)
    generation = models.PositiveBigIntegerField(default=0)
    is_author = models.BooleanField(default=False)

class Audit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='+')
    subject = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='+')
    action = models.CharField(max_length=48)
    scope = models.CharField(max_length=128, blank=True)
    details = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

class Grant(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    contest = models.ForeignKey('judge.Contest', on_delete=models.PROTECT)
    capability = models.CharField(max_length=48)
    grantor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    revoked = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','contest','capability'], name='cpjudge_unique_grant')]

class ImportJob(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    contest = models.ForeignKey('judge.Contest', null=True, blank=True, on_delete=models.PROTECT)
    package_sha256 = models.CharField(max_length=64)
    archive_key = models.CharField(max_length=64)
    status = models.CharField(max_length=20, default='uploaded')
    findings = models.JSONField(default=dict)
    error = models.TextField(blank=True)
    attempt = models.PositiveIntegerField(default=0)
    token = models.CharField(max_length=64,blank=True)
    queued_at = models.DateTimeField(null=True,blank=True)
    started_at = models.DateTimeField(null=True,blank=True)
    finished_at = models.DateTimeField(null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner','package_sha256'], name='cpjudge_owner_package')]

class CollegeIDHistory(models.Model):
    # Reserve old college IDs permanently; corrections cannot release them for reuse.
    college_id = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    reason = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)

class Conflict(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    contest = models.ForeignKey('judge.Contest', on_delete=models.PROTECT)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','contest'],name='cpj_conflict')]

class ExportJob(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    contest = models.ForeignKey('judge.Contest', on_delete=models.PROTECT)
    generation = models.PositiveBigIntegerField()
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, default='queued')
    created = models.DateTimeField(auto_now_add=True)


class ProblemVersion(models.Model):
    """Private coordinator publication; never a worker readiness receipt."""
    job = models.ForeignKey(ImportJob, on_delete=models.PROTECT, related_name='versions')
    attempt = models.PositiveIntegerField()
    token = models.CharField(max_length=64)
    code = models.CharField(max_length=20, unique=True)
    state = models.CharField(max_length=20, default='preparing')
    manifest = models.JSONField(default=dict)
    digest = models.CharField(max_length=64, blank=True)
    problem = models.OneToOneField('judge.Problem', null=True, blank=True, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    published = models.DateTimeField(null=True, blank=True)
    auto_check_status = models.CharField(max_length=16, default='missing')
    auto_check_message = models.CharField(max_length=300, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['job','attempt'], name='cpj_version_attempt')]


class ProbeSolution(models.Model):
    version = models.ForeignKey(ProblemVersion, on_delete=models.PROTECT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)
    runtime = models.ForeignKey('judge.Language', on_delete=models.PROTECT)
    source = models.TextField(max_length=65536)
    sha256 = models.CharField(max_length=64)
    created = models.DateTimeField(auto_now_add=True)

class ProblemProbe(models.Model):
    version = models.ForeignKey(ProblemVersion, on_delete=models.PROTECT)
    solution = models.ForeignKey(ProbeSolution, on_delete=models.PROTECT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    execution = models.OneToOneField('judge.Submission', on_delete=models.PROTECT, related_name='private_probe')
    problem_digest = models.CharField(max_length=64)
    solution_digest = models.CharField(max_length=64)
    runtime_key = models.CharField(max_length=16)
    expires = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)


class EmailLoginPolicy(models.Model):
    # Operational rollback retains all schema/data and changes admission only.
    email_only = models.BooleanField(default=False)


class ContestVersionAdmission(models.Model):
    """Explicit private contest admission; immutable judge manifest stays separate."""
    version = models.ForeignKey(ProblemVersion,on_delete=models.PROTECT)
    contest_problem = models.OneToOneField('judge.ContestProblem',on_delete=models.PROTECT)
    probe = models.ForeignKey(ProblemProbe,on_delete=models.PROTECT)
    runtime = models.ForeignKey('judge.Language',on_delete=models.PROTECT)
    version_digest = models.CharField(max_length=64)
    rules = models.JSONField(default=dict)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    revoked = models.BooleanField(default=False)


class ContestWorkflow(models.Model):
    """Scoped contest metadata; native Contest remains the schedule/scoring store."""
    contest = models.OneToOneField('judge.Contest', on_delete=models.PROTECT, related_name='workflow')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    display_timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    eligibility = models.CharField(max_length=32, default='provisioned')
    published_at = models.DateTimeField(null=True, blank=True)


class ContestProblemLabel(models.Model):
    contest_problem = models.OneToOneField('judge.ContestProblem', on_delete=models.CASCADE, related_name='workflow_label')
    label = models.CharField(max_length=10)


class ContestEntry(models.Model):
    """Registration and access state, independent of native navigation context."""
    contest = models.ForeignKey('judge.Contest', on_delete=models.PROTECT, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    participation = models.OneToOneField('judge.ContestParticipation', on_delete=models.PROTECT, related_name='registration')
    status = models.CharField(max_length=16, default='active', choices=[(x,x) for x in ('active','withdrawn','removed','dq')])
    hidden = models.BooleanField(default=False)
    registered_at = models.DateTimeField()
    changed_at = models.DateTimeField()
    class Meta:
        constraints=[models.UniqueConstraint(fields=['contest','user'],name='cpj_contest_entry_user')]


class ContestReceipt(models.Model):
    """Durable admission; later removal does not invalidate already accepted work."""
    submission = models.OneToOneField('judge.Submission', on_delete=models.PROTECT, related_name='admission_receipt')
    entry = models.ForeignKey(ContestEntry, on_delete=models.PROTECT)
    approval = models.ForeignKey(ContestVersionAdmission, on_delete=models.PROTECT)
    request_key = models.CharField(max_length=36)
    payload_digest = models.CharField(max_length=64)
    version_digest = models.CharField(max_length=64)
    receipt = models.DateTimeField()
    generation = models.PositiveBigIntegerField()
    class Meta:
        constraints=[models.UniqueConstraint(fields=['entry','request_key'],name='cpj_entry_request_key')]


class AuthorTest(models.Model):
    """Private archived native execution; never a ranked participation."""
    execution = models.OneToOneField('judge.Submission', on_delete=models.PROTECT, related_name='author_test')
    approval = models.ForeignKey(ContestVersionAdmission, on_delete=models.PROTECT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.CharField(max_length=36)
    payload_digest = models.CharField(max_length=64)
    version_digest = models.CharField(max_length=64)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner','request_key'], name='cpj_author_test_key')]
