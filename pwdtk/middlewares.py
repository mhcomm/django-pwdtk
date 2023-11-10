import json
import logging


from django.core.exceptions import MiddlewareNotUsed
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

    def __init__(self, get_response=None):

        if not PwdtkSettings.PWDTK_ENABLED:
            logger.debug("PWDTK middleware is disabled")
            raise MiddlewareNotUsed("pwdtk is disabled")
        if get_response:
            super(PwdtkMiddleware, self).__init__(
                get_response=get_response)
        else:
            super(PwdtkMiddleware, self).__init__()

    def process_request(self, request):
        if hasattr(PwdtkSettings, "reset_cache"):
            PwdtkSettings.reset_cache()

    def process_exception(self, request, exception):

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
