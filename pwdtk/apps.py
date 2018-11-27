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
        logger.debug("PWDTK READY")
        import pwdtk.auth_backends_signals  # noqa: F401
        if django.VERSION < (1, 11):
            logger.debug("old django style: try to decorate login function")
            mod_name, obj_name = settings.PWDTK_LOGIN_VIEW.rsplit('.', 1)
            auth_mod = importlib.import_module(mod_name)
            login_func = getattr(auth_mod, obj_name)
            from pwdtk.auth_backends import watch_login
            setattr(auth_mod, obj_name, watch_login(login_func))
            logger.debug("login function decorated")
        # django >= 1.11 can't use auth_views.login, so decorate the view
        elif django.VERSION < (2, 2):
            # TODO: perhaps for newer Djangos we find a wau without monkey
            # TODO: patching
            from pwdtk.auth_backends import watch_login_dispatch
            mod_name, obj_name = settings.PWDTK_LOGIN_VIEW_CLASS.rsplit('.', 1)
            auth_mod = importlib.import_module(mod_name)
            viewclass = getattr(auth_mod, obj_name)
            viewclass.dispatch = watch_login_dispatch(viewclass.dispatch)
            logger.debug("LoginView.dispatch decorated")

        User = get_user_model()
        from pwdtk.watchers import watch_set_password
        User.set_password = watch_set_password(User.set_password)
