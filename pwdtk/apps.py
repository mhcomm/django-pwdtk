import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)

logger.debug("imp pwdtk APPS")


class PwdTkConfig(AppConfig):
    name = 'pwdtk'

    def ready(self):
        """ Install all required hooks for pwdtk
            The required hooks depend on the django version.
        """
        logger.debug("PWDTK READY")
        from django.core.checks import register
        from pwdtk.checks import check_force_renew_on_first_login
        register(check_force_renew_on_first_login)
