from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import json
import logging

from functools import wraps

import minibelt

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied


from django.contrib.auth.backends import ModelBackend

from pwdtk.helpers import get_delta_seconds
from pwdtk.helpers import seconds_to_iso8601
from pwdtk.helpers import PwdtkSettings
from pwdtk.auth_backends_data import UserData

logger = logging.getLogger(__name__)


class PwdtkPermissionDenied(PermissionDenied):
    """ custom exception """

class PwdTkMustChangePassword(Exception):
    """ whenever a user must change his password """

class PwdtkBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

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

        print ("\n\n\n", request, password, username, "\n\n\n")

        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            user_data = UserData(username=username)
            if self.user_is_locked(user_data):

                request.pwdtk_fail = True
                request.pwdtk_fail_reason = "lockout"
                request.pwdtk_user = user_data
                raise PwdtkPermissionDenied

            if user.check_password(password):
                if self.user_must_renew(user_data):
                    request.pwdtk_fail = True
                    request.pwdtk_fail_reason = "pwd_obsolete"
                    request.pwdtk_user = user_data
                    raise PwdTkMustChangePassword
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
                    user_data.save()
                    request.pwdtk_fail = True
                    request.pwdtk_fail_reason = "lockout"
                    request.pwdtk_user = user_data
                    raise PwdtkPermissionDenied
                user_data.save()
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
