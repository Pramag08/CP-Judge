from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('judge', '0153_reconcile_model_metadata')]
    operations = [migrations.AlterField(model_name='contest', name='format_name', field=models.CharField(choices=[('atcoder', 'AtCoder'), ('cpjudge_icpc_v1', 'CPJudge Individual ICPC (20-minute penalty)'), ('default', 'Default'), ('ecoo', 'ECOO'), ('icpc', 'ICPC'), ('ioi', 'IOI (pre-2016)'), ('ioi16', 'IOI')], default='default', help_text='The contest format module to use.', max_length=32, verbose_name='contest format'))]
