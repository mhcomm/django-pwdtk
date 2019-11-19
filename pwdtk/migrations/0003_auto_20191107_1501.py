# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pwdtk', '0002_auto_20191105_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pwddata',
            name='username',
            field=models.CharField(max_length=255, unique=True, null=True),
        ),
    ]
