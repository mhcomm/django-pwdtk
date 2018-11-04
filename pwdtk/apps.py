import logging

import django
from django.apps import AppConfig


logger = logging.getLogger(__name__)


logger.debug("imp pwdtk APPS")  # added trace for dbg of django 1.8 -> django 1.11


class PwdTkConfig(AppConfig):
    name = 'pwdtk'

    def ready(self):
        logger.debug("PWDTK READY")
        import pwdtk.auth_backends_signals  # noqa: F401
        if django.VERSION < (2, ):
            logger.debug("old django style: try to decorate login function")
            from django.contrib.auth import views as auth_views
            from pwdtk.auth_backends import watch_login
            auth_views.login = watch_login(auth_views.login)
            logger.debug("login function decorated")
        # newer django versions don't have auth_views.login, so this function can't be decorated
