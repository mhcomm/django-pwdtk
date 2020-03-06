from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied


from django.contrib.auth.backends import ModelBackend

from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData

logger = logging.getLogger(__name__)


class PwdtkPermissionDenied(PermissionDenied):
    """ custom exception """

class PwdTkMustChangePassword(PermissionDenied):
    """ whenever a user must change his password """

class PwdtkBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def get_or_create_pwd_data_for_user(self, user):
        if not hasattr(user, 'pwdtk_data'):
            user.pwdtk_data = PwdData.objects.create(user=user)

    def authenticate(self, request, password, username=None, **kwargs):

        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            self.get_or_create_pwd_data_for_user(user)
            if user.pwdtk_data.is_locked():
                request.pwdtk_fail = True
                request.pwdtk_fail_reason = "lockout"
                request.pwdtk_user = user.pwdtk_data
                raise PwdtkPermissionDenied

            if user.check_password(password):
                if user.pwdtk_data.must_renew():
                    request.pwdtk_fail = True
                    request.pwdtk_fail_reason = "pwd_obsolete"
                    request.pwdtk_user = user.pwdtk_data
                    raise PwdTkMustChangePassword
                else:
                    if user.pwdtk_data.failed_logins or user.pwdtk_data.fail_time or user.pwdtk_data.locked:
                        user.pwdtk_data.failed_logins = 0
                        user.pwdtk_data.fail_time = None
                        user.pwdtk_data.locked = False
                        user.pwdtk_data.save()
                    return user
            else:
                if PwdtkSettings.PWDTK_USER_FAILURE_LIMIT is None:
                    return None

                if user.pwdtk_data.failed_logins >= PwdtkSettings.PWDTK_USER_FAILURE_LIMIT:
                    user.pwdtk_data.locked = True
                    user.pwdtk_data.fail_time = datetime.datetime.utcnow()
                    user.pwdtk_data.save()
                    request.pwdtk_fail = True
                    request.pwdtk_fail_reason = "lockout"
                    request.pwdtk_user = user.pwdtk_data
                    raise PwdtkPermissionDenied
                else:
                    user.pwdtk_data.failed_logins += 1
                    user.pwdtk_data.save()
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
