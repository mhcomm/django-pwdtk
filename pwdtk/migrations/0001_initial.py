# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from pwdtk.models import json_field


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PwdData',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False,
                    auto_created=True, primary_key=True)),
                ('user_id', models.PositiveIntegerField(
                    default=0, null=True, blank=True)),
                ('username', models.CharField(
                    default=b'', max_length=80, null=True, blank=True)),
                ('data', json_field(default={})),
            ],
        ),
    ]
