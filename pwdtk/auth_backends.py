from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from pwdtk.exceptions import PwdtkForceRenewException
from pwdtk.exceptions import PwdtkLockedException
from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData

logger = logging.getLogger(__name__)


class PwdtkBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

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
            else:
                pwdtk_data.register_failed_login()

        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
            if username and password:
                fake_pwdtk = PwdData.objects.get_or_create(fake_username=username)[0]
                if fake_pwdtk.is_locked():
                    raise PwdtkLockedException(fake_pwdtk)
                fake_pwdtk.register_failed_login()
