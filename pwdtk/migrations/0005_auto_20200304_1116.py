# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.conf import settings
from pwdtk.models import json_field


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pwdtk', '0004_auto_20200304_1114'),
    ]

    operations = [
        migrations.AddField(
            model_name='pwddata',
            name='fail_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='pwddata',
            name='failed_logins',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='pwddata',
            name='last_change_time',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
        migrations.AddField(
            model_name='pwddata',
            name='locked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pwddata',
            name='password_history',
            field=json_field(default=[]),
        ),
        migrations.AddField(
            model_name='pwddata',
            name='user',
            field=models.OneToOneField(
                related_name='pwdtk_data',
                null=True,
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
            ),
        ),
    ]
