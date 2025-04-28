from __future__ import absolute_import
from __future__ import print_function

import datetime
import logging

import django
import pytest


from builtins import range
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import password_changed
from django.contrib.auth.password_validation import validate_password
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.test import Client
from django.test import override_settings
from django.utils import timezone

from pwdtk.tests.fixtures import two_users  # noqa: F401
from pwdtk.helpers import PwdtkSettings


logger = logging.getLogger(__name__)

AUTH_URL = PwdtkSettings.PWDTK_TEST_ADMIN_URL
User = get_user_model()


def change_password(user, password):
    """Change the password using the password validators pipeline"""
    validate_password(password, user)
    user.set_password(password)
    user.save()
    password_changed(password, user)


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
    password = data['password']

    if not use_good_password:
        data['password'] = password + 'a'

    if shall_pass is None:
        shall_pass = use_good_password

    url = AUTH_URL + "login/?next=" + AUTH_URL
    logger.debug("loginurl = %s", url)
    resp = client.post(url, data=data)

    user = auth.get_user(client)
    if django.VERSION < (1, 10):
        is_authenticated = user.is_authenticated()
    else:
        is_authenticated = user.is_authenticated
    if shall_pass:
        assert is_authenticated
    else:
        assert not is_authenticated
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
    csrf_token = resp.cookies.get('csrftoken')
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
    assert resp.status_code == 403

    # Now logging in should fail
    do_login(client, data, shall_pass=False)

    # now let's check out the lockout delay
    # pwdtk data will be populate after first login attempt
    user = User.objects.get(username=username)
    pwdtk_data = user.pwdtk_data
    assert pwdtk_data.locked
    logger.debug("AGE %i", pwdtk_data.fail_age)


@override_settings(
    AUTH_PASSWORD_VALIDATORS=[{
            'NAME': 'pwdtk.validators.PasswordAgeValidator',
    }],
    PWDTK_PASSWD_AGE=30
)
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

    csrf_token = resp.cookies.get('csrftoken')
    # prepare post_data

    password += '1'

    change_password(user, password)

    data = dict(
        username=username,
        password=password,
        csrfmiddlewaretoken=csrf_token,
        )
    do_login(client, data)

    # pwdtk data will be populate after first login
    user = User.objects.get(username=username)
    pwdtk_data = user.pwdtk_data

    # make passwd obsolete
    pwdtk_data.last_change_time = (
        timezone.now() -
        datetime.timedelta(seconds=PwdtkSettings.PWDTK_PASSWD_AGE)
    )
    pwdtk_data.save()
    assert pwdtk_data.compute_must_renew()

    # now login should fail
    do_login(client, data)

    user = User.objects.get(username=username)
    assert user.pwdtk_data.must_renew

    # Make sure we cannot "renew" the password with the exact same password.
    with pytest.raises(ValidationError):
        change_password(user, password)
    assert user.pwdtk_data.must_renew

    password += "2"
    change_password(user, password)
    assert not user.pwdtk_data.must_renew
