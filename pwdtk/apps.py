import importlib
import logging

import django
from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


logger.debug("imp pwdtk APPS")  # added trace for dbg of dj 1.8 -> dj 1.11


class PwdTkConfig(AppConfig):
    name = 'pwdtk'

    def ready(self):
        """ Install all required hooks for pwdtk
            The required hooks depend on the django version.

        """
        # TODO: add hoks only if pwdtk feature needing the hook has been
        # enabled
        logger.debug("PWDTK READY")
        if django.VERSION < (1, 11):
            import pwdtk.sig_receivers  # noqa: F401
            logger.debug("old django style: try to decorate login function")
            mod_name, obj_name = settings.PWDTK_LOGIN_VIEW.rsplit('.', 1)
            auth_mod = importlib.import_module(mod_name)
            login_func = getattr(auth_mod, obj_name)
            from pwdtk.auth_backends import watch_login
            setattr(auth_mod, obj_name, watch_login(login_func))
            # login_func wrapper in order to
            # lockout for tries per user (and redirect to specific page)
            # lockout for password, that's too old (hasn't been changed)
            logger.debug("login function decorated")
            User = get_user_model()
            from pwdtk.watchers import watch_set_password
            User.set_password = watch_set_password(User.set_password)
        # django >= 1.11 can't use auth_views.login, so decorate the view
        elif django.VERSION < (2, 0):
            import pwdtk.sig_receivers  # noqa: F401
            # TODO: perhaps for newer Djangos we find a way without monkey
            # TODO: patching
            User = get_user_model()
            from pwdtk.watchers import watch_set_password
            User.set_password = watch_set_password(User.set_password)
        elif django.VERSION < (2, 2):
            import pwdtk.sig_receivers  # noqa: F401
            # TODO: perhaps for newer Djangos we find a way without monkey
            # TODO: patching
            User = get_user_model()
            from pwdtk.watchers import watch_set_password
            User.set_password = watch_set_password(User.set_password)
        else:
            logger.exception("PWDTK not setup for django >=2.2")
