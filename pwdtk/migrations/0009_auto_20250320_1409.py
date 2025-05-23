# Generated by Django 2.2.28 on 2025-03-20 14:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('pwdtk', '0008_auto_20230905_0835'),
    ]

    operations = [
        migrations.AddField(
            model_name='pwddata',
            name='lockout_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='pwddata',
            name='last_change_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
