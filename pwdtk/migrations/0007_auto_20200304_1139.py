# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('pwdtk', '0006_auto_20200304_1117'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pwddata',
            name='data',
        ),
        migrations.RemoveField(
            model_name='pwddata',
            name='old_user_id',
        ),
        migrations.RemoveField(
            model_name='pwddata',
            name='username',
        ),
        migrations.AlterField(
            model_name='pwddata',
            name='user',
            field=models.OneToOneField(
                related_name='pwdtk_data',
                default=None,
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pwddata',
            name='must_renew',
            field=models.BooleanField(default=False),
        ),
    ]
