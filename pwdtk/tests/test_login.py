from __future__ import absolute_import

import datetime
import logging

import dateutil.parser
import pytest

from builtins import range
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http.response import HttpResponseRedirect
from django.test import Client

from pwdtk.auth_backends_data import UserData


AUTH_URL = settings.PWDTK_TEST_ADMIN_URL
logger = logging.getLogger(__name__)


@pytest.fixture
def two_users():
    """ create two users """
    User = get_user_model()
    users = []
    for ctr in range(2):
        username = 'user%d' % ctr
        passwd = 'pwd%d' % ctr
        usr = User(username=username)
        usr.set_password(passwd)
        usr.is_staff = True
        usr.save()
        logger.debug("create user %r %r", username, passwd)
        users.append((username, passwd))

    return users


@pytest.mark.django_db
def test_login_no_form(two_users):
    browser = "Mozilla/5.0"
    client = Client(browser=browser)

    username, password = two_users[0]

    # First successful login without form
    loggedin = client.login(username=username, password=password)
    print("%s %s -> %s" % (username, password, loggedin))
    assert loggedin is True

    # login with bad password fails without form
    bad_pwd = password + 'a'
    loggedin = client.login(username=username, password=bad_pwd)
    print("%s %s -> %s" % (username, bad_pwd, loggedin))
    assert loggedin is False


@pytest.mark.django_db
def test_login(two_users):
    browser = "Mozilla/5.0"
    client = Client(browser=browser)

    username, password = two_users[0]

    # go to a login page and fetch csrf token
    url = AUTH_URL + "login/?next=" + AUTH_URL
    logger.debug("loginurl = %s", url)
    resp = client.get(url)
    assert hasattr(resp, 'cookies')
    csrf_token = resp.cookies.get('csrf_token')
    logger.debug("token %r", csrf_token)

    # prepare post_data
    data = dict(
        username=username,
        password=password,
        csrfmiddlewaretoken=csrf_token,
        )

    # login once
    do_login(client, data)
    do_logout(client)

    # only two bad logins
    for cnt in range(2):
        logger.debug("bad login %d", cnt)
        resp = do_login(client, data, use_good_password=False)
        assert resp.status_code == 200

    # Now logging in should still work
    do_login(client, data)

    do_logout(client)
    # now 3 bad logins
    for cnt in range(3):
        logger.debug("bad login %d", cnt)
        resp = do_login(client, data, use_good_password=False)
        assert resp.status_code == 200

    # Now logging in should fail
    do_login(client, data, shall_pass=False)

    # now let's check out the lockout delay
    user_data = UserData(username=username)
    logger.debug("userdata : %s", repr(user_data.data))
    assert user_data.locked
    t_fail = dateutil.parser.parse(user_data.fail_time)
    now = datetime.datetime.now()
    delta = now - t_fail
    logger.debug("AGE %s", delta.seconds)


def do_login(client, data, use_good_password=True, shall_pass=None):
    """ helper to simulate logins via the admin login form.
        Logins with good or bad password can be simulated.
        Checks will be performed to see whether login success / failure is
        as expected.
    """
    username = data['username']
    password = data['password']

    if not use_good_password:
        data['password'] = password + 'a'

    if shall_pass is None:
        shall_pass = use_good_password

    url = AUTH_URL + "login/?next=" + AUTH_URL
    logger.debug("loginurl = %s", url)
    resp = client.post(url, data=data)
    status_code = int(resp.status_code)

    if shall_pass:
        assert isinstance(resp, HttpResponseRedirect)
        assert status_code == 302
        assert resp.has_header('location')
        location = resp['location']
        assert location.endswith(settings.PWDTK_TEST_ADMIN_URL)
        logger.debug("login of %r/%r ok as expected",
                     username, password)
    else:
        logger.debug('status_code %s %s', type(status_code), repr(status_code))
        if status_code == 302:
            logger.debug("RESP TYPE %s", type(resp))
            logger.debug("status %s", resp.status_code)
            logger.debug("keys %s", sorted(vars(resp).keys()))
            for key, val in sorted(vars(resp).items()):
                logger.debug("%s: %s", key, repr(val))

            logger.debug("CONTEXT")
            for key, val in sorted(vars(resp.context).items()):
                logger.debug("%s: %s", key, repr(val))
        assert status_code != 302  # no redirection to targert page

        if status_code == 200:
            answer = resp.content
            assert settings.PWDTK_TEST_LOGIN_FAIL_SUBMSG in answer
        else:
            answer = resp.content
            assert settings.PWDTK_TEST_LOCKOUT_SUBMSG in answer

        data['password'] = password  # restore password

    return resp


def do_logout(client):
    """ helper to logout a user via the admin web form """
    url = AUTH_URL + "logout/"
    resp = client.post(url)
    status_code = int(resp.status_code)
    assert status_code in [200, 302]
    logger.debug("logout successful")
