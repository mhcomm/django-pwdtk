from __future__ import absolute_import
from __future__ import print_function

import importlib

import pytest

from django.conf import settings
from django.contrib.auth import get_user_model
from pwdtk.tests.fixtures import two_users  # noqa: F401


User = get_user_model()


@pytest.mark.django_db
def test_pwd_nodflt_hash(two_users):  # noqa: F811
    """ can pwdtk handle a non default pwd hash """
    user = two_users[0]
    username = user.username
    password = user.raw_password
    print("user %s with %r" % (user, password))
    hashers = settings.PASSWORD_HASHERS
    print("hashers:\n%s" % "\n".join(str(hasher) for hasher in hashers))
    salt = ""
    if "django.contrib.auth.hashers.UnsaltedMD5PasswordHasher" in hashers:
        hasher_cls_name = ("django.contrib.auth.hashers"
                           ".UnsaltedMD5PasswordHasher")
    else:
        hasher_cls_name = hashers[-1]
        if hasher_cls_name.endswith("CryptPasswordHasher"):
            salt = "ab"

    assert hasher_cls_name != hashers[0]
    hasher_modname, hasher_name = hasher_cls_name.rsplit(".", 1)
    hasher_mod = importlib.import_module(hasher_modname)
    print("try to import %s:%s" % (hasher_modname, hasher_name))
    hasher = getattr(hasher_mod, hasher_name)()
    print("hasher = ", hasher)
    passwd_hash = hasher.encode(password, salt)
    print("passwd: %s -> %r" % (password, passwd_hash))

    user.password = passwd_hash
    user.save()

    user = User.objects.get(username=username)
    assert user.check_password(password)
