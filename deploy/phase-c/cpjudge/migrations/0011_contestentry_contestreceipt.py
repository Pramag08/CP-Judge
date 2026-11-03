from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion as d

class Migration(migrations.Migration):
    dependencies=[('cpjudge','0010_contestproblemlabel_contestworkflow'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='ContestEntry',fields=[
            ('id',models.AutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('status',models.CharField(choices=[(x,x) for x in ('active','withdrawn','removed','dq')],default='active',max_length=16)),
            ('registered_at',models.DateTimeField()),('changed_at',models.DateTimeField()),
            ('contest',models.ForeignKey(on_delete=d.PROTECT,related_name='registrations',to='judge.contest')),
            ('user',models.ForeignKey(on_delete=d.PROTECT,to=settings.AUTH_USER_MODEL)),
            ('participation',models.OneToOneField(on_delete=d.PROTECT,related_name='registration',to='judge.contestparticipation'))],
            options={'constraints':[models.UniqueConstraint(fields=('contest','user'),name='cpj_contest_entry_user')]}),
        migrations.CreateModel(name='ContestReceipt',fields=[
            ('id',models.AutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('request_key',models.CharField(max_length=36)),('payload_digest',models.CharField(max_length=64)),
            ('version_digest',models.CharField(max_length=64)),('receipt',models.DateTimeField()),('generation',models.PositiveBigIntegerField()),
            ('submission',models.OneToOneField(on_delete=d.PROTECT,related_name='admission_receipt',to='judge.submission')),
            ('entry',models.ForeignKey(on_delete=d.PROTECT,to='cpjudge.contestentry')),
            ('approval',models.ForeignKey(on_delete=d.PROTECT,to='cpjudge.contestversionadmission'))],
            options={'constraints':[models.UniqueConstraint(fields=('entry','request_key'),name='cpj_entry_request_key')]})]
