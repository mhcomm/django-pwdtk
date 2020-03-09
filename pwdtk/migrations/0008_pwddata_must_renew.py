# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pwdtk', '0007_auto_20200304_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='pwddata',
            name='must_renew',
            field=models.BooleanField(default=False),
        ),
    ]
