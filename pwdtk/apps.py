import logging

from django.apps import AppConfig
from django.conf import settings

from pwdtk.helpers import PwdtkSettings
from pwdtk import settings as pwdtk_settings

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

        for password_validator in settings.AUTH_PASSWORD_VALIDATORS:
            if password_validator["NAME"] == getattr(PwdtkSettings, "PWDTK_PASSWORD_VALIDATOR", pwdtk_settings.PWDTK_PASSWORD_VALIDATOR):
                break
        else:
            settings.AUTH_PASSWORD_VALIDATORS.append({
                "NAME": getattr(PwdtkSettings, "PWDTK_PASSWORD_VALIDATOR", pwdtk_settings.PWDTK_PASSWORD_VALIDATOR),
                "OPTIONS": getattr(PwdtkSettings, "PWDTK_PASSWORD_VALIDATOR_OPTIONS", pwdtk_settings.PWDTK_PASSWORD_VALIDATOR_OPTIONS)
            })
