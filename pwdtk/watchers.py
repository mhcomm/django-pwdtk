import datetime
import logging
import os

from pwdtk.helpers import recursion_depth
from pwdtk.settings import PWDTK_PASSWD_HISTORY_LEN


logger = logging.getLogger(__name__)
LOG_PASSWORDS = os.environ.get(
    'PWDTK_LOG_PASSWORDS', 'no')[:1].lower() in 'yt1'


def watch_set_password(orig_set_password):
    """ decorator for set_password functions to
        detect password changes
    """

    if hasattr(orig_set_password, 'pwdtk_decorated'):
        logger.warning("set_password already decorated by pwdtk: %s",
                       repr(orig_set_password.pwdtk_decorated))
        return orig_set_password

    logger.debug("decorating %s", repr(orig_set_password))

    from pwdtk.auth_backends import MHPwdPolicyBackend
    UserData = MHPwdPolicyBackend.get_user_data_cls()

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
            # TODO: instead of detecting a recursion we night try to detect, whether
            # this function si being called during a login. This might be less obscure
            # but perhaps less safe. detecting recursions will always avoid endless
            # recursions
            logger.debug("recursion detected. abandon pwd_change intercept")
            return orig_set_password(self, password)
        changed = not self.check_password(password)
        logger.debug("changed = %s", changed)
        if changed:
            logger.debug("password change detected")
            user_data = UserData(username=self.username)
            pwd_history = user_data.passwd_history
            now = datetime.datetime.now().isoformat()
            orig_set_password(self, password)
            pwd_history.insert(0, (now, self.password))
            pwd_history[PWDTK_PASSWD_HISTORY_LEN:] = []
            user_data.save()
        return orig_set_password(self, password)

    decorated.pwdtk_decorated = True

    return decorated
