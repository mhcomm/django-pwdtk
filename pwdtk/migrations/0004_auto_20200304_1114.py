# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pwdtk', '0003_auto_20191107_1501'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pwddata',
            old_name='user_id',
            new_name='old_user_id',
        ),
    ]
