from __future__ import absolute_import
from __future__ import print_function

import datetime
import logging

import dateutil.parser
import django
import pytest


from builtins import range
from django.http.response import HttpResponseRedirect
from django.test import Client

from pwdtk.tests.fixtures import two_users  # noqa: F401
from pwdtk.helpers import PwdtkSettings


logger = logging.getLogger(__name__)

AUTH_URL = PwdtkSettings.PWDTK_TEST_ADMIN_URL


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
        assert location.endswith(PwdtkSettings.PWDTK_TEST_ADMIN_URL)
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
            logger.debug("T_ADM_URL = %s", PwdtkSettings.PWDTK_TEST_ADMIN_URL)
            logger.debug("location = %s", location)

            assert not location.endswith(PwdtkSettings.PWDTK_TEST_ADMIN_URL)
        elif status_code == 200:
            answer = resp.content
            assert PwdtkSettings.PWDTK_TEST_LOGIN_FAIL_SUBMSG in answer
        else:
            answer = resp.content
            assert PwdtkSettings.PWDTK_TEST_LOCKOUT_SUBMSG in answer

        data['password'] = password  # restore password

    return resp


def do_logout(client):
    """ helper to logout a user via the admin web form """
    url = AUTH_URL + "logout/"
    resp = client.post(url)
    status_code = int(resp.status_code)
    assert status_code in [200, 302]
    logger.debug("logout successful")


@pytest.mark.django_db
def test_login_no_form(two_users):  # noqa: F811
    """ client login without the login url """
    browser = "Mozilla/5.0"
    client = Client(browser=browser)

    user = two_users[0]
    username = user.username
    password = user.raw_password

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

    user = two_users[0]
    username = user.username
    password = user.raw_password

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

    failure_limit = PwdtkSettings.PWDTK_USER_FAILURE_LIMIT
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
    # pwdtk data will be populate after first login attempt
    user.refresh_from_db()
    pwdtk_data = user.pwdtk_data
    assert pwdtk_data.locked
    logger.debug("AGE %s", (datetime.datetime.utcnow() - pwdtk_data.fail_time).total_seconds())


@pytest.mark.django_db
def test_pwd_expire(two_users):  # noqa: F811
    """ test whether a password renewal is demanded if a password
        has not been changed for a given time.
    """

    browser = "Mozilla/5.0"
    client = Client(browser=browser)

    user = two_users[0]
    username = user.username
    password = user.raw_password

    # # go to a login page and fetch csrf token
    url = AUTH_URL + "login/?next=" + AUTH_URL

    resp = client.get(url)

    csrf_token = resp.cookies.get('csrf_token')
    # prepare post_data

    password += '1'
    user.set_password(password)
    user.save()

    data = dict(
        username=username,
        password=password,
        csrfmiddlewaretoken=csrf_token,
        )
    do_login(client, data)

    # pwdtk data will be populate after first login
    user.refresh_from_db()
    pwdtk_data = user.pwdtk_data

    # make passwd obsolete
    pwdtk_data.last_change_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=age)
    pwdtk_data.save()

    # now login should fail
    do_login(client, data, shall_pass=False)
