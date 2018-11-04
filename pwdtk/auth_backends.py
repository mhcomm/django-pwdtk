from __future__ import absolute_import
from __future__ import print_function

import datetime
import json
import logging

import dateutil.parser
import minibelt

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render


logger = logging.getLogger(__name__)
logger.debug("######## Imp backend2")  # for debugging dj 1.8 -> 1.11

PWDTK_USER_FAILURE_LIMIT = settings.PWDTK_USER_FAILURE_LIMIT
PWDTK_IP_FAILURE_LIMIT = settings.PWDTK_IP_FAILURE_LIMIT
PWDTK_LOCKOUT_TIME = settings.PWDTK_LOCKOUT_TIME
PWDTK_LOCKOUT_TEMPLATE = settings.PWDTK_LOCKOUT_TEMPLATE
PWDTK_USER_PARAMS = settings.PWDTK_USER_PARAMS
PWDTK_USERNAME_FORM_FIELD = settings.PWDTK_USERNAME_FORM_FIELD


class MHPwdPolicyBackendError(Exception):
    """ custom exception """


class MHPwdPolicyBackend(object):
    User = None  # cached user model
    UserDataCls = None
    backend = None

    @classmethod
    def get_backend(cls, *args, **kwargs):
        """ gets backend (kind of a singleton) """
        if cls.backend is None:
            cls.backend = cls(*args, **kwargs)
        return cls.backend

    def __init__(self, userdata_cls=None):
        cls = self.__class__
        if cls.UserDataCls is None:
            cls.UserDataCls = minibelt.import_from_path(PWDTK_USER_PARAMS)
        if userdata_cls:
            if isinstance(userdata_cls, str):
                userdata_cls = minibelt.import_from_path(userdata_cls)
        else:
            userdata_cls = cls.UserDataCls

        if not cls.User:
            cls.User = get_user_model()

        self.userdata_cls = userdata_cls

    def user_is_locked(self, username, user_data=None):
        """ determines whether a user is still locked out
        """
        user_data = user_data or self.userdata_cls(username=username)
        if not user_data.locked:
            logger.debug("not locked %d", user_data.failed_logins)
            return False
        t_fail = dateutil.parser.parse(user_data.fail_time)
        t_delta = datetime.datetime.utcnow() - t_fail
        delta_secs = t_delta.days * 86400 + t_delta.seconds
        logger.debug("locked %s %s %s", repr(t_fail), repr(t_delta), repr(delta_secs))
        if delta_secs < PWDTK_LOCKOUT_TIME:
            logger.debug("still locked")
            return True
        logger.debug("no more locked")
        user_data.locked = False
        user_data.save()
        return False

    def check_tries_per_user(self, username):
        """ checks whether a user has more than the allowed amount of failed logins
        """
        cls = self.__class__
        User = cls.User
        users = User.objects.filter(username=username)
        logger.debug("%d USERS: %s", len(users), repr(users))
        if not users:
            return None

        user = users[0]
        user_data = self.userdata_cls(user=user)

        if self.user_is_locked(username, user_data):
            t_fail = dateutil.parser.parse(user_data.fail_time)
            t_delta = datetime.datetime.utcnow() - t_fail
            age = t_delta.days * 86400 + t_delta.seconds
            to_wait = PWDTK_LOCKOUT_TIME - age
            msg = ("user %s entered bad password too often (%d times) (must wait %d seconds)"
                   % (username, user_data.failed_logins, to_wait))
            user_data.failed_logins += 1
            user_data.save()
            logger.warning(msg)  # TODO: convert to INFO if well tested
            raise PermissionDenied(msg)

    def check_tries_per_ip(self, username):
        """ lockout by IP address
            not implemented so far
        """
        # TODO: to be implemented

    def authenticate(self, request=None, username=None, password=None, **kwargs):
        logger.debug(
            "############## MHAUTH: %s %s %s %s",
            repr(request), repr(username), repr(password), repr(kwargs))

        if username and password:
            self.check_tries_per_user(username)
            return  # if check_tries_per_user didn't raise

        if PWDTK_IP_FAILURE_LIMIT and request:
            return self.check_tries_per_ip(request)

    def clear_failed_logins(self, user):
        """ resets lockout info
        """
        logger.debug("clear failed logins for %s", user.username)
        data = self.userdata_cls(user=user)
        data.failed_logins = 0
        data.locked = False
        data.save()

    def handle_failed_login(self, username):
        """ called whenever a login failed
            shall detect failed logins with username and password
            and lock out the user if too many login fails occured
        """
        logger.debug("failed login for %s", username)
        data = self.userdata_cls(username=username)
        data.fail_time = datetime.datetime.utcnow().isoformat()
        data.failed_logins = failed_logins = data.failed_logins + 1
        if failed_logins >= PWDTK_USER_FAILURE_LIMIT:
            data.locked = True
            logger.warning('User %s got logged out after %d login errors ', username,
                           PWDTK_USER_FAILURE_LIMIT)
        data.save()
        return failed_logins


def lockout_response(request, backend, msg=''):
    """ create login response for locked out users
    """
    username = request.POST.get(PWDTK_USERNAME_FORM_FIELD, '')
    context = {
        'failure_limit': PWDTK_USER_FAILURE_LIMIT,
        'username': username,
        'msg': msg,
    }

    if PWDTK_LOCKOUT_TIME:
        context.update({'cooloff_time':
                       seconds_to_iso8601(PWDTK_LOCKOUT_TIME)})

        user_data = backend.userdata_cls(username=username)
        t_fail = dateutil.parser.parse(user_data.fail_time)
        t_delta = datetime.datetime.utcnow() - t_fail
        age = t_delta.days * 86400 + t_delta.seconds
        to_wait = PWDTK_LOCKOUT_TIME - age
        to_wait_str = "%d minutes and %d seconds" % (
            to_wait // 60, to_wait % 60)
        context['to_wait'] = to_wait_str

    logger.debug("CTX: %s", context)

    if request.is_ajax():
        return HttpResponse(
            json.dumps(context),
            content_type='application/json',
            status=403,
        )
    if PWDTK_LOCKOUT_TEMPLATE:
        return render(request, PWDTK_LOCKOUT_TEMPLATE, context, status=403)


def watch_login(login_func):
    """ allows to decorate the login function in order to create a custon
        respoonse for logged out users.
        This is required for old django versions, that don't receive the
        request object with a user_login_failed signa
    """
    # Don't decorate multiple times
    if login_func.__name__ == 'new_login':
        return login_func

    def new_login(request, *args, **kwargs):
        backend = MHPwdPolicyBackend.get_backend()

        if request.method != 'POST':
            return login_func(request, *args, **kwargs)

        logger.debug("intercepting POST to login")
        username = request.POST[PWDTK_USERNAME_FORM_FIELD]
        try:
            backend.check_tries_per_user(username)
            return login_func(request, *args, **kwargs)
        except PermissionDenied as exc:
            logger.debug("login blocked %s %s", repr(exc), repr(vars(exc)))
            msg = "arx"
            return lockout_response(request, backend, msg)

        logger.debug("calling login with %s, %s and %s", repr(request), repr(args), repr(kwargs))
        rslt = login_func(request, *args, **kwargs)
        logger.debug("login returned %s", repr(rslt))
        return rslt

    return new_login


def seconds_to_iso8601(seconds):
    """ helper to convert seconds to iso string """
    # split seconds to larger units
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    days, hours, minutes = map(int, (days, hours, minutes))
    seconds = round(seconds, 6)

    # ## build date
    date = ''
    if days:
        date = '%sD' % days

    # ## build time
    time = u'T'
    # hours
    bigger_exists = date or hours
    if bigger_exists:
        time += '{:02}H'.format(hours)
    # minutes
    bigger_exists = bigger_exists or minutes
    if bigger_exists:
        time += '{:02}M'.format(minutes)
    # seconds
    if seconds.is_integer():
        seconds = '{:02}'.format(int(seconds))
    else:
        # 9 chars long w/leading 0, 6 digits after decimal
        seconds = '%09.6f' % seconds
    # remove trailing zeros
    seconds = seconds.rstrip('0')
    time += '{}S'.format(seconds)
    return u'P' + date + time
