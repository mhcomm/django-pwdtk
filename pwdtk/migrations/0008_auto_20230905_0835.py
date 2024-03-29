# Generated by Django 2.2.28 on 2023-09-05 08:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('pwdtk', '0007_auto_20200304_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='pwddata',
            name='fake_username',
            field=models.CharField(max_length=150, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='pwddata',
            name='user',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pwdtk_data',
                to=settings.AUTH_USER_MODEL),
        ),
    ]
