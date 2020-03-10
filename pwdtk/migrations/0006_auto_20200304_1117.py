# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def fill_pwd_data(apps, schema_editor):

    PwdData = apps.get_model("pwdtk", "pwddata")
    for pwd_data in PwdData.objects.all():
        pwd_data.user_id = pwd_data.old_user_id
        pwd_data.locked = pwd_data.data.get("locked", False)
        pwd_data.failed_logins = pwd_data.data.get("failed_logins", 0)
        pwd_data.fail_time = pwd_data.data.get("fail_time")
        pwd_data.password_history = pwd_data.data.get('passwd_history', [])
        if pwd_data.password_history:
            pwd_data.last_change_time = pwd_data.password_history[0][0]
        pwd_data.save()


class Migration(migrations.Migration):

    dependencies = [
        ('pwdtk', '0005_auto_20200304_1116'),
    ]

    operations = [
        migrations.RunPython(
            fill_pwd_data,
            reverse_code=migrations.RunPython.noop),
    ]
