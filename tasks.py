import re
import os

import django

from django.contrib.auth import get_user_model

from invoke import task


BASEDIR = os.path.realpath(os.path.dirname(__file__))

MANAGE_CMD = None


def setup_django():
    django.setup()


def get_manage_cmd():
    global MANAGE_CMD
    if MANAGE_CMD is None:
        dj_settings = os.environ.get(
            'DJANGO_SETTINGS_MODULE', 'pwdtk.testproject.dj18.settings')
        match = re.match(r'^.*\.dj(\d+)\..*$', dj_settings)
        MANAGE_CMD = os.path.join(
            BASEDIR,
            "pwdtk/testproject/manage%s.py" % match.groups(1))

    return MANAGE_CMD


@task(name="initdb")
def initdb(ctx):
    setup_django()
    manage = get_manage_cmd()
    ctx.run(manage + " migrate")
    User = get_user_model()
    if User.objects.all().count() == 0:
        print("create a superuser")
        ctx.run(
            manage
            + " createsuperuser --username admin "
            "--noinput --email admin@localhost")
        admin = User.objects.get(username='admin')
        admin.set_password("admin")
        admin.save()
