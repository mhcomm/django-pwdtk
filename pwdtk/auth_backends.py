from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData

logger = logging.getLogger(__name__)


class PwdtkBaseException(Exception):

    def __init__(self, pwdtk_data):

        self.pwdtk_data = pwdtk_data


class PwdtkLockedException(PwdtkBaseException):
    """ custom exception """


class PwdtkForceRenewException(PwdtkBaseException):
    """ custom exception """


class PwdtkBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """
    def compute_failed_login(self, pwdtk_data):

        if PwdtkSettings.PWDTK_USER_FAILURE_LIMIT is None:
            return None
        if pwdtk_data.failed_logins+1 >= PwdtkSettings.PWDTK_USER_FAILURE_LIMIT:
            pwdtk_data.set_locked(pwdtk_data.failed_logins+1)
            raise PwdtkLockedException(pwdtk_data)
        else:
            pwdtk_data.failed_logins += 1
            pwdtk_data.save()

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not PwdtkSettings.PWDTK_ENABLED:
            return
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            pwdtk_data = PwdData.get_or_create_for_user(user)
            if pwdtk_data.is_locked():
                raise PwdtkLockedException(pwdtk_data)
            if user.check_password(password) and self.user_can_authenticate(user):
                must_renew = pwdtk_data.compute_must_renew()
                if (pwdtk_data.failed_logins or pwdtk_data.fail_time or
                   pwdtk_data.locked or must_renew != pwdtk_data.must_renew):
                    pwdtk_data.failed_logins = 0
                    pwdtk_data.fail_time = None
                    pwdtk_data.locked = False
                    pwdtk_data.must_renew = must_renew
                    pwdtk_data.save()
                if must_renew and not kwargs.get("ignore_must_renew"):
                    raise PwdtkForceRenewException(pwdtk_data)
                return user

            self.compute_failed_login(pwdtk_data)

        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
            if username and password:
                fake_pwdtk = PwdData.objects.get_or_create(fake_username=username)[0]
                if fake_pwdtk.is_locked():
                    raise PwdtkLockedException(fake_pwdtk)
                self.compute_failed_login(fake_pwdtk)
