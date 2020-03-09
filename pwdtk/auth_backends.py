from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied


from django.contrib.auth.backends import ModelBackend

from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData

logger = logging.getLogger(__name__)

class PwdtkPermissionDenied(PermissionDenied):
    """ custom exception """


class PwdtkBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """
    def authenticate(self, request, password, username=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            pwdtk_data = PwdData.get_or_create_for_user(user)
            request.pwdtk_user = pwdtk_data
            if pwdtk_data.is_locked():
                request.pwdtk_fail = True
                request.pwdtk_fail_reason = "lockout"
                request.pwdtk_user = pwdtk_data
                raise PwdtkPermissionDenied
            if user.check_password(password):
                must_renew = pwdtk_data.compute_must_renew()
                if (pwdtk_data.failed_logins or pwdtk_data.fail_time or
                  pwdtk_data.locked or must_renew != pwdtk_data.must_renew):
                    pwdtk_data.failed_logins = 0
                    pwdtk_data.fail_time = None
                    pwdtk_data.locked = False
                    pwdtk_data.must_renew = must_renew
                    pwdtk_data.save()
                return user
            else:
                if PwdtkSettings.PWDTK_USER_FAILURE_LIMIT is None:
                    return None
                if pwdtk_data.failed_logins > PwdtkSettings.PWDTK_USER_FAILURE_LIMIT:
                    pwdtk_data.set_locked()
                    request.pwdtk_fail = True
                    request.pwdtk_fail_reason = "lockout"
                    request.pwdtk_user = pwdtk_data
                    raise PwdtkPermissionDenied
                else:
                    pwdtk_data.failed_logins += 1
                    pwdtk_data.save()
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
