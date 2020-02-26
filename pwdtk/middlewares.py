import json
import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from pwdtk.auth_backends import lockout_response
from pwdtk.auth_backends import MHPwdPolicyBackend


logger = logging.getLogger(__name__)
PWDTK_PASSWD_CHANGE_VIEW = settings.PWDTK_PASSWD_CHANGE_VIEW


class PwdtkMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        if not settings.PWDTK_ENABLED:
            logger.debug("PWDTK middleware is disabled")
            raise MiddlewareNotUsed("pwdtk is disabled")
        super(PwdtkMiddleware, self).__init__(get_response)

    def process_request(self, request):
        logger.debug("PWDTK Proc Req %s %s", request.user, repr(request))
        request.pwdtk_fail_user = None
        request.pwdtk_fail_reason = None

    def process_response(self, request, response):
        logger.debug(
            "PWDTK Proc resp %s %s %s",
            request.user, repr(request), repr(response))
        if request.pwdtk_fail_user:
            fail_reason = request.pwdtk_fail_reason
            context = {
                'username': request.pwdtk_fail_user,
                'fail_reason': fail_reason
                }
            if fail_reason == "lockout":
                context.update({
                    'msg': 'user locked out (too many bad passwords)',
                    })
            if fail_reason == "pwd_obsolete":
                context.update({
                    'msg': 'user must renew password',
                    })
            if request.is_ajax():
                return HttpResponse(
                    json.dumps(context),
                    content_type='application/json',
                    status=403,
                    )
            logger.debug("SHOULD REDIRECT for %s", request.pwdtk_fail_user)
            if fail_reason == "lockout":
                backend = MHPwdPolicyBackend.get_backend()
                return lockout_response(request, backend)
            if fail_reason == "pwd_obsolete":
                return redirect(PWDTK_PASSWD_CHANGE_VIEW)
        return response
