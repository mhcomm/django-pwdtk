from __future__ import absolute_import
from __future__ import print_function

import logging

import pytest

from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


@pytest.fixture
def two_users():
    """ create two users with two passwords """
    User = get_user_model()
    users = []
    for ctr in range(2):
        username = 'user%d' % ctr
        passwd = 'pwd%d' % ctr
        usr = User(username=username)
        usr.save()
        usr.set_password(passwd)
        usr.is_staff = True
        usr.save()
        usr.raw_password = passwd
        logger.debug("create user %r %r", username, passwd)
        users.append(usr)

    return users
