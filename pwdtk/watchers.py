import datetime
import logging

from pwdtk.auth_backends_settings import PWDTK_PASSWD_HISTORY_LEN


logger = logging.getLogger(__name__)


def watch_set_password(orig_set_password):
    """ decorator for set_password functions to
        detect password changes
    """
    logger.debug("decorating %s", repr(orig_set_password))

    from pwdtk.auth_backends import MHPwdPolicyBackend
    UserData = MHPwdPolicyBackend.get_user_data_cls()

    def decorated(self, password):
        logger.debug("changing password %s %s", self.username, repr(password))
        changed = not self.check_password(password)
        if changed:
            logger.debug("password change detected")
            user_data = UserData(username=self.username)
            pwd_history = user_data.passwd_history
            now = datetime.datetime.now().isoformat()
            orig_set_password(self, password)
            pwd_history.insert(0, (now, self.password))
            pwd_history[PWDTK_PASSWD_HISTORY_LEN:] = []
            user_data.save()

    return decorated
