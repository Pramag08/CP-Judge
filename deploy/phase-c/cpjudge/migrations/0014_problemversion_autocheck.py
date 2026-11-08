from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cpjudge', '0013_contestentry_hidden')]

    operations = [
        migrations.AddField(model_name='problemversion', name='auto_check_status', field=models.CharField(default='missing', max_length=16)),
        migrations.AddField(model_name='problemversion', name='auto_check_message', field=models.CharField(blank=True, max_length=300)),
    ]
