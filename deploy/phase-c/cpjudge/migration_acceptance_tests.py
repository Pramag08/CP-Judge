"""Isolated additive migration and non-destructive operational rollback proof."""
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from cpjudge.models import Audit,Identity
from cpjudge.email_identity import stage_keys,set_mode,provision_email

class MigrationAcceptance(TransactionTestCase):
 def test_forward_migrations_and_rollback_preserve_intervening_rows(self):
  U=get_user_model();admin=U.objects.create_superuser('migration-operator',email='migration@example.invalid',password='Preserved-Password-17!')
  original=admin.password
  latest=MigrationExecutor(connection).loader.graph.leaf_nodes('cpjudge')
  # Rehearse schema generation from prior checkpoint in the isolated test DB.
  executor=MigrationExecutor(connection);executor.migrate([('cpjudge','0006_problemversion')])
  try:
   executor=MigrationExecutor(connection);executor.migrate(latest)
  finally:
   executor=MigrationExecutor(connection);executor.migrate(latest)
  admin.refresh_from_db();self.assertEqual(admin.password,original)
  stage_keys(admin);set_mode(admin,True,'Isolated migration rehearsal')
  user,pw=provision_email(admin,'intervening-migration@example.invalid');user.set_password('New-Intervening-31!');user.save(update_fields=['password'])
  mark=Audit.objects.create(actor=admin,subject=user,action='test.migration')
  from judge.models import Profile,Problem,ProblemGroup,Language,Submission,SubmissionSource
  Profile.objects.get_or_create(user=user)
  group=ProblemGroup.objects.create(name='rollback',full_name='Rollback fixture')
  problem=Problem.objects.create(code='rollbackfixture',name='Rollback',group=group,description='Fixture',points=1,time_limit=1,memory_limit=65536)
  language=Language.objects.create(key='RB',name='Fixture',short_name='RB',common_name='RB',extension='rb',ace='text',pygments='text')
  sub=Submission.objects.create(user=user.profile,problem=problem,language=language,status='D',result='WA')
  source=SubmissionSource.objects.create(submission=sub,source='synthetic rollback fixture')
  before={m._meta.label:list(m.objects.all().values()) for m in (U,Identity,Submission,SubmissionSource,Audit)}
  set_mode(admin,False,'Rollback admission only; retain additive schema and all intervening data')
  for model in (U,Submission,SubmissionSource):self.assertEqual(list(model.objects.all().values()),before[model._meta.label])
  self.assertTrue(Audit.objects.filter(pk=mark.pk).exists());self.assertTrue(Identity.objects.filter(user=user,canonical_email=user.email).exists())
