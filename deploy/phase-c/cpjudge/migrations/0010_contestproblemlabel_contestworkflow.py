from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('cpjudge','0009_contestversionadmission'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='ContestProblemLabel',fields=[
            ('id',models.AutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('label',models.CharField(max_length=10)),
            ('contest_problem',models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name='workflow_label',to='judge.contestproblem'))]),
        migrations.CreateModel(name='ContestWorkflow',fields=[
            ('id',models.AutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('display_timezone',models.CharField(default='Asia/Kolkata',max_length=64)),
            ('eligibility',models.CharField(default='provisioned',max_length=32)),
            ('published_at',models.DateTimeField(blank=True,null=True)),
            ('contest',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name='workflow',to='judge.contest')),
            ('owner',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL))]),
    ]
