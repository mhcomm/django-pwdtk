#!/usr/bin/env python

# ############################################################################
# Name       : pwdtk.tests.test_renew
"""
  Summary    : Test the three modes demanding the renewal of a password:
               the age of the password, PWDTK_FORCE_RENEW_ON_FIRST_LOGIN
               and the force_renew of the integrating tool
"""
# #############################################################################

import contextlib
import datetime
import json
import logging
import warnings

import pytest

from django.contrib.auth import get_user_model
from django.core.checks.registry import registry
from django.core.exceptions import ValidationError
from django.test import Client
from django.test import override_settings
from django.utils import timezone

from pwdtk.checks import check_force_renew_on_first_login
from pwdtk.exceptions import PwdtkConfigWarning
from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData
from pwdtk.tests.fixtures import two_users  # noqa: F401
from pwdtk.tests.test_login import change_password
from pwdtk.tests.test_login import do_login
from pwdtk.tests.test_login import do_logout
from pwdtk.tests.test_login import get_login_data


logger = logging.getLogger(__name__)

BROWSER = "Mozilla/5.0"
User = get_user_model()

# only the age validator is needed to reset must_renew on a password change
AGE_VALIDATOR_ONLY = override_settings(
    AUTH_PASSWORD_VALIDATORS=[{
            'NAME': 'pwdtk.validators.PasswordAgeValidator',
    }],
)


def assert_needs_renew(resp):
    """ helper checking that a login was refused to renew the password
        :param resp: response of the login attempt
    """
    assert resp.status_code == 403
    assert json.loads(resp.content) == {"status": "PWDTK_NEED_RENEW_PASSWORD"}


@contextlib.contextmanager
def no_config_warning():
    """ helper turning any pwdtk configuration warning into an error """
    with warnings.catch_warnings():
        warnings.simplefilter("error", PwdtkConfigWarning)
        yield


# PWDTK_FORCE_RENEW_ON_FIRST_LOGIN
# ----------------------------------------------------------


@pytest.mark.django_db
def test_no_force_renew_on_first_login(two_users):  # noqa: F811
    """ PWDTK_FORCE_RENEW_ON_FIRST_LOGIN is off by default, so a first login
        does not demand a password renewal
    """
    assert PwdtkSettings.PWDTK_FORCE_RENEW_ON_FIRST_LOGIN is False

    client = Client(browser=BROWSER)
    user = two_users[0]

    do_login(client, get_login_data(client, user))
    do_logout(client)

    assert not PwdData.objects.get(user=user).must_renew


@override_settings(PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True)
@pytest.mark.django_db
def test_force_renew_on_first_login(two_users):  # noqa: F811
    """ with PWDTK_FORCE_RENEW_ON_FIRST_LOGIN the first login is refused and
        a password renewal is demanded although the password is correct
    """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    # no pwdtk data exists as long as the user never tried to log in
    assert not PwdData.objects.filter(user=user).exists()

    assert_needs_renew(do_login(client, data, shall_pass=False))

    # the pwdtk data created by the first login attempt demands a renewal
    pwdtk_data = PwdData.objects.get(user=user)
    assert pwdtk_data.must_renew
    assert pwdtk_data.compute_must_renew()

    # a refused login is no failed login and must not lock the account
    assert pwdtk_data.failed_logins == 0
    assert not pwdtk_data.locked

    # the renewal keeps being demanded as long as the password is unchanged
    assert_needs_renew(do_login(client, data, shall_pass=False))


@override_settings(PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True)
@pytest.mark.django_db
def test_force_renew_on_first_login_bad_password(two_users):  # noqa: F811
    """ a renewal forced on the first login does not hide a bad password """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    resp = do_login(client, data, use_good_password=False)
    assert resp.status_code == 200

    pwdtk_data = PwdData.objects.get(user=user)
    assert pwdtk_data.must_renew
    assert pwdtk_data.failed_logins == 1


@AGE_VALIDATOR_ONLY
@override_settings(PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True)
@pytest.mark.django_db
def test_force_renew_on_first_login_renewed(two_users):  # noqa: F811
    """ renewing the password lifts the renewal forced on the first login and
        the renewal is not demanded again by the following logins
    """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    assert_needs_renew(do_login(client, data, shall_pass=False))

    data['password'] = user.raw_password + '1'
    change_password(user, data['password'])
    assert not PwdData.objects.get(user=user).must_renew

    # the renewal is only forced when the pwdtk data is created, hence all
    # the logins following the renewal pass
    do_login(client, data)
    do_logout(client)
    do_login(client, data)
    do_logout(client)

    assert not PwdData.objects.get(user=user).must_renew


@pytest.mark.django_db
def test_no_force_renew_for_setup_user(two_users):  # noqa: F811
    """ a user who is already set up, i.e. who already owns pwdtk data,
        just logs in without any renewal even if
        PWDTK_FORCE_RENEW_ON_FIRST_LOGIN is enabled afterwards
    """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    # this first login sets the user up while the setting is still off
    do_login(client, data)
    do_logout(client)
    assert not PwdData.objects.get(user=user).must_renew

    with override_settings(PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True):
        do_login(client, data)
        do_logout(client)

    assert not PwdData.objects.get(user=user).must_renew


# renewal forced by the integrating tool
# ----------------------------------------------------------


@pytest.mark.django_db
def test_force_renew_action(two_users):  # noqa: F811
    """ the integrating tool forces the renewal of the password of a user
        who is already set up. The next login is refused although the
        password is correct
    """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    do_login(client, data)
    do_logout(client)

    PwdData.get_or_create_for_user(user).force_renew()

    assert_needs_renew(do_login(client, data, shall_pass=False))

    pwdtk_data = PwdData.objects.get(user=user)
    assert pwdtk_data.must_renew

    # a refused login is no failed login and must not lock the account
    assert pwdtk_data.failed_logins == 0
    assert not pwdtk_data.locked

    # the renewal keeps being demanded as long as the password is unchanged
    assert_needs_renew(do_login(client, data, shall_pass=False))

    # the other user is not impacted
    other_client = Client(browser=BROWSER)
    other_user = two_users[1]
    do_login(other_client, get_login_data(other_client, other_user))
    do_logout(other_client)
    assert not PwdData.objects.get(user=other_user).must_renew


@pytest.mark.django_db
def test_force_renew_action_before_first_login(two_users):  # noqa: F811
    """ the integrating tool forces the renewal of the password of a user
        who never logged in. The pwdtk data is created on the fly and the
        first login is refused
    """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    assert not PwdData.objects.filter(user=user).exists()

    PwdData.get_or_create_for_user(user).force_renew()
    assert PwdData.objects.get(user=user).must_renew

    assert_needs_renew(do_login(client, data, shall_pass=False))


@pytest.mark.django_db
def test_force_renew_action_bad_password(two_users):  # noqa: F811
    """ a renewal forced by the integrating tool does not hide
        a bad password
    """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    PwdData.get_or_create_for_user(user).force_renew()

    resp = do_login(client, data, use_good_password=False)
    assert resp.status_code == 200

    pwdtk_data = PwdData.objects.get(user=user)
    assert pwdtk_data.must_renew
    assert pwdtk_data.failed_logins == 1


@AGE_VALIDATOR_ONLY
@pytest.mark.django_db
def test_force_renew_action_renewed(two_users):  # noqa: F811
    """ renewing the password lifts the renewal forced by the integrating
        tool and the renewal is not demanded again by the following logins
    """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    PwdData.get_or_create_for_user(user).force_renew()

    assert_needs_renew(do_login(client, data, shall_pass=False))

    data['password'] = user.raw_password + '1'
    change_password(user, data['password'])
    assert not PwdData.objects.get(user=user).must_renew

    do_login(client, data)
    do_logout(client)
    do_login(client, data)
    do_logout(client)

    assert not PwdData.objects.get(user=user).must_renew


# missing PasswordAgeValidator
# ----------------------------------------------------------


@pytest.mark.django_db
def test_force_renew_warns_without_age_validator(two_users):  # noqa: F811
    """ forcing a renewal without any active PasswordAgeValidator warns,
        as nothing would ever reset must_renew
    """
    pwdtk_data = PwdData.get_or_create_for_user(two_users[0])

    with pytest.warns(PwdtkConfigWarning, match="PasswordAgeValidator"):
        pwdtk_data.force_renew()

    # the renewal is forced nevertheless
    assert PwdData.objects.get(user=two_users[0]).must_renew


@AGE_VALIDATOR_ONLY
@pytest.mark.django_db
def test_force_renew_does_not_warn_with_age_validator(two_users):  # noqa: F811
    """ forcing a renewal does not warn as long as a PasswordAgeValidator
        is active
    """
    pwdtk_data = PwdData.get_or_create_for_user(two_users[0])

    with no_config_warning():
        pwdtk_data.force_renew()

    assert PwdData.objects.get(user=two_users[0]).must_renew


@override_settings(PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True)
@pytest.mark.django_db
def test_force_renew_on_first_login_warns(two_users):  # noqa: F811
    """ a renewal forced on the first login warns as well """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    with pytest.warns(PwdtkConfigWarning, match="PasswordAgeValidator"):
        assert_needs_renew(do_login(client, data, shall_pass=False))


# system check
# ----------------------------------------------------------


def test_check_is_registered():
    """ the system check is registered by the app config """
    assert check_force_renew_on_first_login in registry.get_checks()


@pytest.mark.django_db
def test_check_without_force_renew_on_first_login():
    """ nothing to check as long as PWDTK_FORCE_RENEW_ON_FIRST_LOGIN is off,
        even without any active PasswordAgeValidator
    """
    assert check_force_renew_on_first_login(None) == []


@override_settings(PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True)
@pytest.mark.django_db
def test_check_force_renew_on_first_login_without_age_validator():
    """ PWDTK_FORCE_RENEW_ON_FIRST_LOGIN without any active
        PasswordAgeValidator is reported
    """
    warns = check_force_renew_on_first_login(None)

    assert [warn.id for warn in warns] == ['pwdtk.W001']
    assert 'PWDTK_FORCE_RENEW_ON_FIRST_LOGIN' in warns[0].msg
    assert 'PasswordAgeValidator' in warns[0].hint


@AGE_VALIDATOR_ONLY
@override_settings(PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True)
@pytest.mark.django_db
def test_check_force_renew_on_first_login_with_age_validator():
    """ PWDTK_FORCE_RENEW_ON_FIRST_LOGIN is fine with an active
        PasswordAgeValidator
    """
    assert check_force_renew_on_first_login(None) == []


@override_settings(PWDTK_ENABLED=False, PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True)
@pytest.mark.django_db
def test_check_pwdtk_disabled():
    """ nothing to check as long as pwdtk is disabled """
    assert check_force_renew_on_first_login(None) == []


# interactions with the age of the password
# ----------------------------------------------------------


def age_validators(*max_ages):
    """ helper activating one PasswordAgeValidator per given max_age
        :param max_ages: max_age of each validator, in seconds
    """
    return override_settings(
        AUTH_PASSWORD_VALIDATORS=[{
            'NAME': 'pwdtk.validators.PasswordAgeValidator',
            'OPTIONS': {'max_age': max_age},
        } for max_age in max_ages],
        )


def make_password_old(pwdtk_data, age):
    """ helper aging the password of a given pwdtk data
        :param pwdtk_data: pwdtk data of the user
        :param age: age of the password to simulate, in seconds
    """
    pwdtk_data.last_change_time = (
        timezone.now() - datetime.timedelta(seconds=age))
    pwdtk_data.save()


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
    client = Client(browser=BROWSER)

    user = two_users[0]
    username = user.username
    password = user.raw_password

    data = get_login_data(client, user)

    password += '1'

    change_password(user, password)
    data['password'] = password

    do_login(client, data)

    # pwdtk data will be populate after first login
    user = User.objects.get(username=username)
    pwdtk_data = user.pwdtk_data

    # make passwd obsolete
    make_password_old(pwdtk_data, PwdtkSettings.PWDTK_PASSWD_AGE)
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


@age_validators(0)
@pytest.mark.django_db
def test_max_age_zero_disables_the_age_mode(two_users):  # noqa: F811
    """ max_age set to 0 never demands a renewal, whatever the age of
        the password
    """
    pwdtk_data = PwdData.get_or_create_for_user(two_users[0])

    make_password_old(pwdtk_data, 10 * 365 * 24 * 3600)
    assert not pwdtk_data.compute_must_renew()


@age_validators(3600, 60)
@pytest.mark.django_db
def test_smallest_max_age_wins(two_users):  # noqa: F811
    """ the smallest max_age of the active validators is applied """
    pwdtk_data = PwdData.get_or_create_for_user(two_users[0])

    make_password_old(pwdtk_data, 90)
    assert pwdtk_data.compute_must_renew()


@age_validators(3600, 0)
@pytest.mark.django_db
def test_max_age_zero_wins_over_the_others(two_users):  # noqa: F811
    """ a single max_age set to 0 disables the age mode altogether """
    pwdtk_data = PwdData.get_or_create_for_user(two_users[0])

    make_password_old(pwdtk_data, 7200)
    assert not pwdtk_data.compute_must_renew()


@age_validators(0)
@override_settings(PWDTK_FORCE_RENEW_ON_FIRST_LOGIN=True)
@pytest.mark.django_db
def test_force_renew_on_first_login_without_expiry(two_users):  # noqa: F811
    """ the documented setup of a renewal demanded on the first login
        without expiring the passwords afterwards
    """
    client = Client(browser=BROWSER)
    user = two_users[0]
    data = get_login_data(client, user)

    # the validator is active, hence no configuration warning
    with no_config_warning():
        assert_needs_renew(do_login(client, data, shall_pass=False))

    # the renewal lifts the demand although max_age is 0
    data['password'] = user.raw_password + '1'
    change_password(user, data['password'])
    assert not PwdData.objects.get(user=user).must_renew

    do_login(client, data)
    do_logout(client)

    # and the password never expires
    pwdtk_data = PwdData.objects.get(user=user)
    make_password_old(pwdtk_data, 10 * 365 * 24 * 3600)
    assert not pwdtk_data.compute_must_renew()


@age_validators(60)
@pytest.mark.django_db
def test_disable_must_renew_exempts_the_user(two_users):  # noqa: F811
    """ a truthy disable_must_renew on the user object exempts him from
        any renewal, whatever the mode demanding it
    """
    user = two_users[0]
    pwdtk_data = PwdData.get_or_create_for_user(user)

    pwdtk_data.force_renew()
    make_password_old(pwdtk_data, 90)
    assert pwdtk_data.compute_must_renew()

    pwdtk_data.user.disable_must_renew = True
    assert not pwdtk_data.compute_must_renew()
