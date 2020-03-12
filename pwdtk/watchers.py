import logging
import os

from functools import wraps

from django.utils import timezone

from pwdtk.helpers import recursion_depth
from pwdtk.helpers import PwdtkSettings
from pwdtk.signals import pwd_data_post_change_password


logger = logging.getLogger(__name__)
LOG_PASSWORDS = os.environ.get(
    'PWDTK_LOG_PASSWORDS', 'no')[:1].lower() in 'yt1'


def watch_set_password(orig_set_password):
    """ decorator for set_password functions to
        detect password changes
    """

    if hasattr(orig_set_password, '_decorated_by_pwdtk'):
        logger.warning("set_password already decorated by pwdtk")
        return orig_set_password

    logger.debug("decorating %s", repr(orig_set_password))

    # from pwdtk.auth_backends import MHPwdPolicyBackend
    # UserData = MHPwdPolicyBackend.get_user_data_cls()

    @wraps(orig_set_password)
    def decorated(self, password):
        passwd_str = password if LOG_PASSWORDS else '********'
        logger.debug(
            "potential passwd change detected %r %s",
            self.username,
            repr(passwd_str),
            )
        # logging in if a user has a pwd hash, that isn't default
        # causes a weird recursion
        depth = recursion_depth()

        if not self.username:
            logger.debug("no username specified. Watcher has nothing to do")
            return orig_set_password(self, password)
        if depth > 0:
            # TODO: instead of detecting a recursion we might try to detect,
            # whether this function si being called during a login. This
            # might be less obscure but perhaps less safe. detecting
            # recursions will always avoid endless recursions
            logger.debug("recursion detected. abandon pwd_change intercept")
            return orig_set_password(self, password)
        changed = not self.check_password(password)
        logger.debug("changed = %s", changed)
        if changed:
            logger.debug("password change detected")
            orig_set_password(self, password)
            if hasattr(self, 'pwdtk_data'):
                now = timezone.now()
                self.pwdtk_data.password_history.insert(
                    0, (now, self.password))
                self.pwdtk_data.password_history[
                    PwdtkSettings.PWDTK_PASSWD_HISTORY_LEN:] = []
                self.pwdtk_data.last_change_time = now
                self.pwdtk_data.must_renew = False
                self.pwdtk_data.save()
                pwd_data_post_change_password.send(
                    sender=self.pwdtk_data.__class__,
                    pwd_data=self.pwdtk_data)
        return orig_set_password(self, password)

    decorated._decorated_by_pwdtk = True

    return decorated
