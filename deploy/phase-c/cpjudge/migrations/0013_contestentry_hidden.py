from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cpjudge', '0012_authortest')]

    operations = [migrations.AddField(model_name='contestentry', name='hidden', field=models.BooleanField(default=False))]
