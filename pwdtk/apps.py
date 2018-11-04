import logging

import django
from django.apps import AppConfig
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


logger.debug("imp pwdtk APPS")  # added trace for dbg of dj 1.8 -> dj 1.11


class PwdTkConfig(AppConfig):
    name = 'pwdtk'

    def ready(self):
        logger.debug("PWDTK READY")
        import pwdtk.auth_backends_signals  # noqa: F401
        if django.VERSION < (1, 11):
            logger.debug("old django style: try to decorate login function")
            from django.contrib.auth import views as auth_views
            from pwdtk.auth_backends import watch_login
            auth_views.login = watch_login(auth_views.login)
            logger.debug("login function decorated")
        # django >= 1.11 can't use auth_views.login, so decorate the view
        elif django.VERSION < (2, 2):
            # TODO: perhaps for newer djangos we find a wau without monkey
            # TODO: patching
            from django.contrib.auth.views import LoginView
            from pwdtk.auth_backends import watch_login_dispatch
            LoginView.dispatch = watch_login_dispatch(LoginView.dispatch)
            logger.debug("LoginView.dispatch decorated")

        User = get_user_model()
        from pwdtk.watchers import watch_set_password
        User.set_password = watch_set_password(User.set_password)
