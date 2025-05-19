# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def uniqify_pwd_data(apps, schema_editor):
    """ finds multiple entries for same username and keeps only one

        This is required prior to adding a unique contraint to
        the PwdData / unique field
    """
    db = schema_editor.connection.alias
    PwdData = apps.get_model("pwdtk", "PwdData")

    usr_w_cnt = PwdData.objects.using(db).all().values('username').annotate(
        ucnt=models.Count("username")).filter(ucnt__gt=1)

    for username in usr_w_cnt.values_list("username", flat=True):
        print("removing redundant PwdData entries for %r" % username)
        to_rm = PwdData.objects.using(db).filter(username=username).order_by("pk")[1:]
        for usr in to_rm:
            usr.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pwdtk', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(uniqify_pwd_data),
    ]
