#!/usr/bin/env python

# ############################################################################
# Name       : pwdtk.tests.test_lockout
"""
  Summary    : Test the lockout of an account after too many logins with a
               bad password, as well as its unlock, either after a successful
               login or as an action made by the integrating tool
"""
# #############################################################################

import datetime
import json
import logging

import pytest

from django.contrib.auth import get_user_model
from django.test import Client
from django.test import override_settings
from django.utils import timezone

from pwdtk.exceptions import PwdtkLockedException
from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData
from pwdtk.models import make_tz_aware
from pwdtk.tests.fixtures import two_users  # noqa: F401
from pwdtk.tests.test_login import do_login
from pwdtk.tests.test_login import get_login_data


logger = logging.getLogger(__name__)

BROWSER = "Mozilla/5.0"
UNKNOWN_USER = "nobody"
PASSWORD = "pwd"
User = get_user_model()

# a first lockout lasts 60s, the next ones 120s, 240s, ... without any limit
LOCKOUT_DELAYS = override_settings(
    PWDTK_USER_FAILURE_LIMIT=3,
    PWDTK_LOCKOUT_TIME=60,
    PWDTK_LOCKOUT_MULTIPLIER=2,
    PWDTK_MAX_LOCKOUT_TIME=0,
    )


def bad_password(user):
    """ helper building a bad password of a given user
        :param user: user object as created by the two_users fixture
    """
    return user.raw_password + 'a'


def do_bad_logins(client, user, count):
    """ helper logging in with a bad password without getting locked out
        :param client: client object
        :param user: user object as created by the two_users fixture
        :param count: number of logins to perform
    """
    for cnt in range(count):
        logger.debug("bad login %d", cnt)
        assert not client.login(
            username=user.username, password=bad_password(user))


def lock_account(client, user):
    """ helper locking an account with too many logins with a bad password
        :param client: client object
        :param user: user object as created by the two_users fixture
        :returns: the pwdtk data of the locked user
    """
    do_bad_logins(client, user, PwdtkSettings.PWDTK_USER_FAILURE_LIMIT - 1)
    with pytest.raises(PwdtkLockedException):
        client.login(username=user.username, password=bad_password(user))

    pwdtk_data = PwdData.objects.get(user=user)
    assert pwdtk_data.is_locked()
    return pwdtk_data


def do_bad_logins_for_unknown_user(client, count):
    """ helper logging in with a user name matching no user
        :param client: client object
        :param count: number of logins to perform
    """
    for cnt in range(count):
        logger.debug("bad login %d", cnt)
        assert not client.login(username=UNKNOWN_USER, password=PASSWORD)


def lock_unknown_user(client):
    """ helper locking a user name matching no user
        :param client: client object
        :returns: the pwdtk data of the locked user name
    """
    do_bad_logins_for_unknown_user(
        client, PwdtkSettings.PWDTK_USER_FAILURE_LIMIT - 1)
    with pytest.raises(PwdtkLockedException):
        client.login(username=UNKNOWN_USER, password=PASSWORD)

    pwdtk_data = PwdData.objects.get(fake_username=UNKNOWN_USER)
    assert pwdtk_data.is_locked()
    return pwdtk_data


def expire_lockout(pwdtk_data):
    """ helper simulating the expiry of a lockout
        :param pwdtk_data: pwdtk data of the locked user
    """
    pwdtk_data.locked_until = timezone.now() - datetime.timedelta(seconds=1)
    pwdtk_data.save()


def assert_locked_for(pwdtk_data, lockout_time, since):
    """ helper checking the expiry date of a lockout
        :param pwdtk_data: pwdtk data of the locked user
        :param lockout_time: expected duration of the lockout, in seconds
        :param since: date taken just before the lockout was set
    """
    delay = datetime.timedelta(seconds=lockout_time)
    assert since + delay <= pwdtk_data.locked_until <= timezone.now() + delay


# -------------------- logins with a bad password ---------------------------

@pytest.mark.django_db
def test_bad_password_is_registered(two_users):  # noqa: F811
    """ a login with a bad password is counted and dated """
    user = two_users[0]
    client = Client(browser=BROWSER)
    since = timezone.now()

    do_bad_logins(client, user, 1)

    pwdtk_data = PwdData.objects.get(user=user)
    assert pwdtk_data.failed_logins == 1
    assert since <= pwdtk_data.fail_time <= timezone.now()
    assert not pwdtk_data.locked
    assert not pwdtk_data.is_locked()


@LOCKOUT_DELAYS
@pytest.mark.django_db
def test_lockout_at_the_failure_limit(two_users):  # noqa: F811
    """ an account is locked as soon as the failure limit is reached """
    user = two_users[0]
    client = Client(browser=BROWSER)
    failure_limit = PwdtkSettings.PWDTK_USER_FAILURE_LIMIT
    since = timezone.now()

    do_bad_logins(client, user, failure_limit - 1)
    assert not PwdData.objects.get(user=user).is_locked()

    with pytest.raises(PwdtkLockedException) as exc_info:
        client.login(username=user.username, password=bad_password(user))

    pwdtk_data = PwdData.objects.get(user=user)
    assert exc_info.value.pwdtk_data.pk == pwdtk_data.pk
    assert pwdtk_data.locked
    assert pwdtk_data.failed_logins == failure_limit
    assert_locked_for(pwdtk_data, PwdtkSettings.PWDTK_LOCKOUT_TIME, since)
    assert pwdtk_data.is_locked()


@override_settings(PWDTK_USER_FAILURE_LIMIT=0)
@pytest.mark.django_db
def test_no_lockout_without_failure_limit(two_users):  # noqa: F811
    """ a failure limit of zero disables the lockout """
    user = two_users[0]
    client = Client(browser=BROWSER)

    do_bad_logins(client, user, 5)

    pwdtk_data = PwdData.objects.get(user=user)
    assert pwdtk_data.failed_logins == 5
    assert not pwdtk_data.locked
    assert not pwdtk_data.is_locked()


# -------------------- logins with an unknown user name ---------------------

@pytest.mark.django_db
def test_bad_username_is_registered():
    """ a login with a user name matching no user is counted and dated """
    client = Client(browser=BROWSER)
    since = timezone.now()

    do_bad_logins_for_unknown_user(client, 1)

    pwdtk_data = PwdData.objects.get(fake_username=UNKNOWN_USER)
    assert pwdtk_data.user is None
    assert pwdtk_data.failed_logins == 1
    assert since <= pwdtk_data.fail_time <= timezone.now()
    assert not pwdtk_data.is_locked()


@pytest.mark.django_db
def test_bad_username_without_password_is_ignored():
    """ a login without any password leaves no trace """
    client = Client(browser=BROWSER)

    assert not client.login(username=UNKNOWN_USER, password="")

    assert not PwdData.objects.exists()


@LOCKOUT_DELAYS
@pytest.mark.django_db
def test_lockout_of_an_unknown_user():
    """ a user name matching no user is locked out as well """
    client = Client(browser=BROWSER)
    since = timezone.now()

    pwdtk_data = lock_unknown_user(client)

    assert pwdtk_data.user is None
    assert pwdtk_data.locked
    assert pwdtk_data.failed_logins == PwdtkSettings.PWDTK_USER_FAILURE_LIMIT
    assert_locked_for(pwdtk_data, PwdtkSettings.PWDTK_LOCKOUT_TIME, since)

    # a further login attempt is refused instead of being counted
    with pytest.raises(PwdtkLockedException):
        client.login(username=UNKNOWN_USER, password=PASSWORD)
    pwdtk_data.refresh_from_db()
    assert pwdtk_data.failed_logins == PwdtkSettings.PWDTK_USER_FAILURE_LIMIT


@pytest.mark.django_db
def test_unlock_of_an_unknown_user():
    """ the lockout of a user name matching no user can be lifted too """
    client = Client(browser=BROWSER)
    pwdtk_data = lock_unknown_user(client)

    assert pwdtk_data.unlock() is True

    # the login attempts are counted again instead of being refused
    do_bad_logins_for_unknown_user(client, 1)
    pwdtk_data.refresh_from_db()
    assert pwdtk_data.failed_logins == 1
    assert not pwdtk_data.is_locked()


@pytest.mark.django_db
def test_lockout_of_an_unknown_user_is_dropped_once_he_exists():
    """ the failed logins of an unknown user name are not held against the
        user finally created with that name
    """
    client = Client(browser=BROWSER)
    lock_unknown_user(client)

    user = User(username=UNKNOWN_USER)
    user.set_password(PASSWORD)
    user.save()

    assert client.login(username=UNKNOWN_USER, password=PASSWORD)

    assert not PwdData.objects.filter(fake_username=UNKNOWN_USER).exists()
    assert PwdData.objects.get(user=user).failed_logins == 0


# -------------------- duration of a lockout --------------------------------

@pytest.mark.parametrize("failed_logins, lockout_time", [
    (3, 60),
    (4, 120),
    (5, 240),
    ])
@LOCKOUT_DELAYS
@pytest.mark.django_db
def test_lockout_time_grows_with_each_lockout(
        two_users, failed_logins, lockout_time):  # noqa: F811
    """ each failed login beyond the limit multiplies the lockout time """
    pwdtk_data = PwdData.get_or_create_for_user(two_users[0])
    pwdtk_data.failed_logins = failed_logins
    since = timezone.now()

    pwdtk_data.set_locked()

    pwdtk_data.refresh_from_db()
    assert pwdtk_data.locked
    assert_locked_for(pwdtk_data, lockout_time, since)


@override_settings(
    PWDTK_USER_FAILURE_LIMIT=3,
    PWDTK_LOCKOUT_TIME=60,
    PWDTK_LOCKOUT_MULTIPLIER=2,
    PWDTK_MAX_LOCKOUT_TIME=100,
    )
@pytest.mark.django_db
def test_lockout_time_is_capped(two_users):  # noqa: F811
    """ a lockout never lasts longer than PWDTK_MAX_LOCKOUT_TIME """
    pwdtk_data = PwdData.get_or_create_for_user(two_users[0])
    pwdtk_data.failed_logins = 5
    since = timezone.now()

    pwdtk_data.set_locked()

    assert_locked_for(pwdtk_data, PwdtkSettings.PWDTK_MAX_LOCKOUT_TIME, since)


# -------------------- expiry of a lockout ----------------------------------

@pytest.mark.django_db
def test_lockout_expires(two_users):  # noqa: F811
    """ a lockout is lifted once its expiry date is passed """
    user = two_users[0]
    client = Client(browser=BROWSER)
    pwdtk_data = lock_account(client, user)

    expire_lockout(pwdtk_data)

    assert not pwdtk_data.is_locked()
    pwdtk_data.refresh_from_db()
    assert not pwdtk_data.locked
    # the failed logins are kept to make the next lockout last longer
    assert pwdtk_data.failed_logins == PwdtkSettings.PWDTK_USER_FAILURE_LIMIT


# -------------------- unlock as an action of the integrating tool ----------

@pytest.mark.django_db
def test_unlock_lifts_a_lockout(two_users):  # noqa: F811
    """ a lockout can be lifted before its expiry """
    user = two_users[0]
    client = Client(browser=BROWSER)
    pwdtk_data = lock_account(client, user)

    assert pwdtk_data.unlock() is True

    pwdtk_data.refresh_from_db()
    assert not pwdtk_data.locked
    assert pwdtk_data.failed_logins == 0
    assert pwdtk_data.fail_time is None
    assert pwdtk_data.locked_until is None
    assert not pwdtk_data.is_locked()


@pytest.mark.django_db
def test_unlock_allows_to_log_in_again(two_users):  # noqa: F811
    """ an unlocked user does not have to wait for the end of his lockout """
    user = two_users[0]
    client = Client(browser=BROWSER)
    pwdtk_data = lock_account(client, user)

    pwdtk_data.unlock()

    assert client.login(username=user.username, password=user.raw_password)


@pytest.mark.django_db
def test_unlock_resets_the_failed_logins(two_users):  # noqa: F811
    """ an account not locked yet gets its failure count cleared as well """
    user = two_users[0]
    client = Client(browser=BROWSER)
    do_bad_logins(client, user, 1)
    pwdtk_data = PwdData.objects.get(user=user)
    assert not pwdtk_data.locked

    assert pwdtk_data.unlock() is True

    pwdtk_data.refresh_from_db()
    assert pwdtk_data.failed_logins == 0
    assert pwdtk_data.fail_time is None


@pytest.mark.django_db
def test_unlock_of_a_clean_account_changes_nothing(
        two_users, django_assert_num_queries):  # noqa: F811
    """ unlocking an account without any failed login hits no database """
    user = two_users[0]
    client = Client(browser=BROWSER)
    assert client.login(username=user.username, password=user.raw_password)
    pwdtk_data = PwdData.objects.get(user=user)

    with django_assert_num_queries(0):
        assert pwdtk_data.unlock() is False


@pytest.mark.django_db
def test_unlock_keeps_must_renew(two_users):  # noqa: F811
    """ unlocking an account does not lift a forced password renewal """
    user = two_users[0]
    client = Client(browser=BROWSER)
    pwdtk_data = lock_account(client, user)
    pwdtk_data.force_renew()

    assert pwdtk_data.unlock() is True

    pwdtk_data.refresh_from_db()
    assert pwdtk_data.must_renew


# -------------------- lockout at login -------------------------------------

@pytest.mark.django_db
def test_login_is_refused_while_locked(two_users):  # noqa: F811
    """ a locked user cannot log in, even with his right password """
    user = two_users[0]
    client = Client(browser=BROWSER)
    lock_account(client, user)

    with pytest.raises(PwdtkLockedException):
        client.login(username=user.username, password=user.raw_password)


@pytest.mark.django_db
def test_login_resets_the_failed_logins(two_users):  # noqa: F811
    """ a successful login clears the failed logins of a user """
    user = two_users[0]
    client = Client(browser=BROWSER)
    do_bad_logins(client, user, 1)

    assert client.login(username=user.username, password=user.raw_password)

    pwdtk_data = PwdData.objects.get(user=user)
    assert pwdtk_data.failed_logins == 0
    assert pwdtk_data.fail_time is None


@pytest.mark.django_db
def test_login_after_a_lockout_expiry(two_users):  # noqa: F811
    """ a login once a lockout expired leaves no lockout data behind """
    user = two_users[0]
    client = Client(browser=BROWSER)
    pwdtk_data = lock_account(client, user)
    expire_lockout(pwdtk_data)

    assert client.login(username=user.username, password=user.raw_password)

    pwdtk_data.refresh_from_db()
    assert not pwdtk_data.locked
    assert pwdtk_data.failed_logins == 0
    assert pwdtk_data.fail_time is None
    assert pwdtk_data.locked_until is None


@override_settings(PWDTK_ENABLED=False)
@pytest.mark.django_db
def test_no_failed_login_registered_when_pwdtk_is_disabled(two_users):  # noqa: F811
    """ a disabled pwdtk does not count the logins with a bad password """
    user = two_users[0]
    client = Client(browser=BROWSER)

    do_bad_logins(client, user, PwdtkSettings.PWDTK_USER_FAILURE_LIMIT)

    assert not PwdData.objects.exists()


@pytest.mark.django_db
def test_no_lockout_check_when_pwdtk_is_disabled(two_users):  # noqa: F811
    """ a disabled pwdtk lets a locked user log in """
    user = two_users[0]
    client = Client(browser=BROWSER)
    lock_account(client, user)

    with override_settings(PWDTK_ENABLED=False):
        assert client.login(
            username=user.username, password=user.raw_password)


# -------------------- lockout report ---------------------------------------

@pytest.mark.django_db
def test_lockout_context(two_users):  # noqa: F811
    """ the context of a lockout describes it entirely """
    user = two_users[0]
    client = Client(browser=BROWSER)
    pwdtk_data = lock_account(client, user)

    assert pwdtk_data.get_lockout_context() == {
        "username": user.username,
        "failed_logins": PwdtkSettings.PWDTK_USER_FAILURE_LIMIT,
        "fail_time": make_tz_aware(pwdtk_data.fail_time).isoformat(),
        "locked_until": make_tz_aware(pwdtk_data.locked_until).isoformat(),
        }


@pytest.mark.django_db
def test_lockout_context_of_an_unknown_user():
    """ the context of a lockout falls back on the attempted user name """
    client = Client(browser=BROWSER)
    pwdtk_data = lock_unknown_user(client)

    assert pwdtk_data.get_lockout_context() == {
        "username": UNKNOWN_USER,
        "failed_logins": PwdtkSettings.PWDTK_USER_FAILURE_LIMIT,
        "fail_time": make_tz_aware(pwdtk_data.fail_time).isoformat(),
        "locked_until": make_tz_aware(pwdtk_data.locked_until).isoformat(),
        }


@pytest.mark.django_db
def test_lockout_response(two_users):  # noqa: F811
    """ a login refused by a lockout is answered with its context """
    user = two_users[0]
    client = Client(browser=BROWSER)
    data = get_login_data(client, user)
    failure_limit = PwdtkSettings.PWDTK_USER_FAILURE_LIMIT

    for cnt in range(failure_limit - 1):
        logger.debug("bad login %d", cnt)
        resp = do_login(client, data, use_good_password=False)
        assert resp.status_code == 200

    resp = do_login(client, data, use_good_password=False)

    assert resp.status_code == 403
    assert resp["Content-Type"] == "application/json"
    pwdtk_data = PwdData.objects.get(user=user)
    assert json.loads(resp.content) == dict(
        pwdtk_data.get_lockout_context(), status="PWDTK_LOCKED")

    # the right password does not help anymore
    resp = do_login(client, data, shall_pass=False)
    assert resp.status_code == 403
    assert json.loads(resp.content)["status"] == "PWDTK_LOCKED"


@pytest.mark.django_db
def test_lockout_response_of_an_unknown_user(two_users):  # noqa: F811
    """ a login refused by the lockout of an unknown user name is answered
        with its context as well
    """
    client = Client(browser=BROWSER)
    data = dict(get_login_data(client, two_users[0]), username=UNKNOWN_USER)
    failure_limit = PwdtkSettings.PWDTK_USER_FAILURE_LIMIT

    for cnt in range(failure_limit - 1):
        logger.debug("bad login %d", cnt)
        resp = do_login(client, data, shall_pass=False)
        assert resp.status_code == 200

    resp = do_login(client, data, shall_pass=False)

    assert resp.status_code == 403
    pwdtk_data = PwdData.objects.get(fake_username=UNKNOWN_USER)
    assert json.loads(resp.content) == dict(
        pwdtk_data.get_lockout_context(), status="PWDTK_LOCKED")
