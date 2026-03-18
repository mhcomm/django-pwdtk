import json
import logging

from django.http import HttpResponse

try:
    from django.utils.deprecation import MiddlewareMixin
except: # noqa E722
    class MiddlewareMixin(object):
        pass

from pwdtk.auth_backends import PwdtkForceRenewException
from pwdtk.auth_backends import PwdtkLockedException
from pwdtk.helpers import PwdtkSettings

logger = logging.getLogger(__name__)


class PwdtkMiddleware(MiddlewareMixin):

    def process_request(self, request):
        # Will still be called even if PwdtkSettings.PWDTK_ENABLED is False.
        # Only use safe code here or add a conditional on
        # PwdtkSettings.PWDTK_ENABLED when necessary to keep the logic sound.
        if hasattr(PwdtkSettings, "reset_cache"):
            PwdtkSettings.reset_cache()

    def process_exception(self, request, exception):
        # Will still be called even if PwdtkSettings.PWDTK_ENABLED is False.
        # Only use safe code here or add a conditional on
        # PwdtkSettings.PWDTK_ENABLED when necessary to keep the logic sound.

        if isinstance(exception, PwdtkLockedException):
            context = exception.pwdtk_data.get_lockout_context()
            context["status"] = "PWDTK_LOCKED"
            return HttpResponse(
                json.dumps(context),
                content_type='application/json',
                status=403,
                )

        if isinstance(exception, PwdtkForceRenewException):
            return HttpResponse(
                json.dumps({"status": "PWDTK_NEED_RENEW_PASSWORD"}),
                content_type='application/json',
                status=403,
                )

        return None
