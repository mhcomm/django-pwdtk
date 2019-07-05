from __future__ import absolute_import
from __future__ import print_function

import datetime
import logging

import dateutil.parser
import django
import pytest


from builtins import range
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http.response import HttpResponseRedirect
from django.test import Client

from pwdtk.auth_backends import MHPwdPolicyBackend
from pwdtk.tests.fixtures import two_users  # noqa: F401


logger = logging.getLogger(__name__)

AUTH_URL = settings.PWDTK_TEST_ADMIN_URL
UserData = MHPwdPolicyBackend.get_user_data_cls()


def do_login(client, data, use_good_password=True, shall_pass=None):
    """ helper to simulate logins via the admin login form.
        Logins with good or bad password can be simulated.
        Checks will be performed to see whether login success / failure is
        as expected.
        :param client: client object
        :param data: form data (username, password, csrf_token, ...)
        :param use_good_password: if set to false a bad password will be used
        :param shall_pass:  indicates the expacted behaviour
                            (failed login, passed login)
                            If set to None, then it is set to use_good_password
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

    location = None
    if status_code == 302:
        location = resp['location']

    logger.debug("LOCATION %s", location)

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

            if resp.context:
                logger.debug("CONTEXT")
                for key, val in sorted(vars(resp.context).items()):
                    logger.debug("%s: %s", key, repr(val))
            else:
                logger.debug("NO CONTEXT")

        if status_code == 302:  # should not pass
            logger.debug("T_ADM_URL = %s", settings.PWDTK_TEST_ADMIN_URL)
            logger.debug("location = %s", location)

            assert not location.endswith(settings.PWDTK_TEST_ADMIN_URL)
        elif status_code == 200:
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


def change_passwd(username, password):
    """ changes password of a user """
    User = get_user_model()
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()


def set_password_age(username, age, offset=0):
    user_data = UserData(username=username)
    pwd_hist = user_data.passwd_history
    entry = pwd_hist[offset]
    entry_date = (datetime.datetime.now() - datetime.timedelta(seconds=age))
    entry[0] = entry_date.isoformat()
    user_data.save()


@pytest.mark.django_db
def test_login_no_form(two_users):  # noqa: F811
    """ client login without the login url """
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
def test_login(two_users):  # noqa: F811
    """ login via the login url """
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

    failure_limit = settings.PWDTK_USER_FAILURE_LIMIT
    if not failure_limit:
        logger.debug("PWDTK_USER_FAILURE_LIMIT not set. will skip test")
        return

    # only two bad logins
    for cnt in range(failure_limit - 1):
        logger.debug("bad login %d", cnt)
        resp = do_login(client, data, use_good_password=False)
        assert resp.status_code == 200

    # Now logging in should still work
    do_login(client, data)

    do_logout(client)
    # now two bad logins
    for cnt in range(failure_limit - 1):
        logger.debug("bad login %d", cnt)
        resp = do_login(client, data, use_good_password=False)
        assert resp.status_code == 200

    # Now the final bad login
    resp = do_login(client, data, use_good_password=False)
    if django.VERSION < (1, 11):
        assert resp.status_code == 200
    else:
        assert resp.status_code == 403

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


@pytest.mark.django_db
def test_pwd_expire(two_users):  # noqa: F811
    """ test whether a password renewal is demanded if a password
        has not been changed for a given time.
    """

    browser = "Mozilla/5.0"
    client = Client(browser=browser)

    username, password = two_users[0]
    user_data = UserData(username=username)

    pwd_hist = user_data.passwd_history
    print("PWD_HIST = ", len(pwd_hist), pwd_hist)

    # # go to a login page and fetch csrf token
    url = AUTH_URL + "login/?next=" + AUTH_URL

    resp = client.get(url)

    csrf_token = resp.cookies.get('csrf_token')
    # prepare post_data

    password += '1'
    change_passwd(username, password)

    data = dict(
        username=username,
        password=password,
        csrfmiddlewaretoken=csrf_token,
        )
    do_login(client, data)

    user_data = UserData(username=username)
    pwd_hist = user_data.passwd_history
    print("PWD_HIST = ", len(pwd_hist), pwd_hist)

    # make passwd obsolete
    set_password_age(username, settings.PWDTK_PASSWD_AGE + 1)

    user_data = UserData(username=username)
    pwd_hist = user_data.passwd_history
    print("PWD_HIST = ", len(pwd_hist), pwd_hist)

    # now login should fail
    do_login(client, data, shall_pass=False)
