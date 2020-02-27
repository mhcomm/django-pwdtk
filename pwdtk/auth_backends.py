from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import json
import logging

from functools import wraps

import dateutil.parser
import minibelt

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render

from django.contrib.auth.backends import ModelBackend

from pwdtk.helpers import get_delta_seconds
from pwdtk.helpers import seconds_to_iso8601
from pwdtk.helpers import PwdtkSettings

logger = logging.getLogger(__name__)


class PwdtkPermissionDenied(PermissionDenied):
    """ custom exception """

class PwdTkMustChangePassword(Exception):
    """ whenever a user must change his password """

class PwdtkBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """
    UserDataCls = None
    def __init__(self, userdata_cls=None):
        cls = self.__class__
        if userdata_cls:
            if isinstance(userdata_cls, str):
                userdata_cls = minibelt.import_from_path(userdata_cls)
        else:
            userdata_cls = cls.get_user_data_cls()

        self.userdata_cls = userdata_cls

    @classmethod
    def get_user_data_cls(cls):
        if not cls.UserDataCls:
            cls.UserDataCls = minibelt.import_from_path(PwdtkSettings.PWDTK_USER_PARAMS)
        return cls.UserDataCls

    def user_is_locked(self, user_data):
        """ determines whether a user is still locked out
        """
        if not user_data.locked:
            logger.debug("not locked %d", user_data.failed_logins)
            return False
        delta_secs = get_delta_seconds(user_data.fail_time)
        logger.debug("locked %s %s",
                     user_data.fail_time, delta_secs)
        if delta_secs < PwdtkSettings.PWDTK_LOCKOUT_TIME:
            logger.debug("still locked")
            return True
        logger.debug("no more locked")
        user_data.locked = False
        user_data.save()
        return False

    def user_must_renew(self, user_data):
        """ determines whether a user must renew his password
        """
        history = user_data.passwd_history
        if not history:
            return False
        change_delta = get_delta_seconds(history[0][0])
        return change_delta > PwdtkSettings.PWDTK_PASSWD_AGE

    def authenticate(self, request, password, username=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            user_data = self.userdata_cls(username=username)
            if self.user_is_locked(user_data):
                request.pwdtk_fail_user = username
                request.pwdtk_fail_reason = "lockout"
                raise PwdtkPermissionDenied

            if user.check_password(password):
                if self.user_must_renew(user_data):
                    request.pwdtk_fail_user = username
                    request.pwdtk_fail_reason = "pwd_obsolete"
                    raise PwdTkMustChangePassword("user %s must change his password" % username)
                else:
                    user_data.failed_logins = 0
                    user_data.locked = False
                    user_data.save()
                    return user
            else:
                if PwdtkSettings.PWDTK_USER_FAILURE_LIMIT is None:
                    return None
                user_data.failed_logins += 1
                user_data.fail_time = datetime.datetime.utcnow().isoformat()
                if user_data.failed_logins >= PwdtkSettings.PWDTK_USER_FAILURE_LIMIT:
                    user_data.locked = True
                    request.pwdtk_fail_user = username
                    request.pwdtk_fail_reason = "lockout"
                    raise PwdtkPermissionDenied
                user_data.save()
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)




def lockout_response(request, backend, msg=''):
    """ create login response for locked out users
    """
    username = request.POST.get(PwdtkSettings.PWDTK_USERNAME_FORM_FIELD, '')
    context = {
        'failure_limit': PwdtkSettings.PWDTK_USER_FAILURE_LIMIT,
        'username': username,
        'msg': msg,
    }

    if PwdtkSettings.PWDTK_LOCKOUT_TIME:
        context.update({'cooloff_time':
                       seconds_to_iso8601(PwdtkSettings.PWDTK_LOCKOUT_TIME)})

        user_data = backend.userdata_cls(username=username)
        t_fail = dateutil.parser.parse(user_data.fail_time)
        t_delta = datetime.datetime.utcnow() - t_fail
        age = t_delta.days * 86400 + t_delta.seconds
        to_wait = PwdtkSettings.PWDTK_LOCKOUT_TIME - age
        to_wait_minutes, to_wait_seconds = divmod(to_wait, 60)
        to_wait_str = "%d minutes and %d seconds" % (
            to_wait_minutes, to_wait_seconds)
        context['to_wait'] = to_wait_str
        context['to_wait_time_tuple'] = (to_wait_minutes, to_wait_seconds)

    logger.debug("CTX: %s", context)

    if request.is_ajax():
        return HttpResponse(
            json.dumps(context),
            content_type='application/json',
            status=403,
        )
    if PwdtkSettings.PWDTK_LOCKOUT_TEMPLATE:
        return render(request, PwdtkSettings.PWDTK_LOCKOUT_TEMPLATE, context, status=403)


def change_passwd_response(request, backend, msg=''):
    """ create login response for locked out users
    """
    username = request.POST.get(PwdtkSettings.PWDTK_USERNAME_FORM_FIELD, '')
    context = {
        'max_passwd_age': PwdtkSettings.PWDTK_PASSWD_AGE,
        'username': username,
        'msg': msg,
    }

    logger.debug("CTX: %s", context)

    if request.is_ajax():
        return HttpResponse(
            json.dumps(context),
            content_type='application/json',
            status=403,
        )

    if PwdtkSettings.PWDTK_PASSWD_CHANGE_TEMPLATE:
        return render(
            request, PwdtkSettings.PWDTK_PASSWD_CHANGE_TEMPLATE, context, status=403)

    return redirect(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW)
