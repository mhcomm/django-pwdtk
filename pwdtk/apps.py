import logging

from django.apps import AppConfig
from django.contrib.auth import get_user_model

from pwdtk.helpers import PwdtkSettings

logger = logging.getLogger(__name__)


logger.debug("imp pwdtk APPS")  # added trace for dbg of dj 1.8 -> dj 1.11


class PwdTkConfig(AppConfig):
    name = 'pwdtk'

    def ready(self):
        """ Install all required hooks for pwdtk
            The required hooks depend on the django version.

        """
        logger.debug("PWDTK READY")
        if not PwdtkSettings.PWDTK_ENABLED:
            logger.debug("PWDTK DISABLED")
            return

        User = get_user_model()
        from pwdtk.watchers import watch_set_password
        User.set_password = watch_set_password(User.set_password)
