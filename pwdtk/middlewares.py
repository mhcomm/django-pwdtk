import json
import logging

from six.moves.urllib.parse import urlencode

from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django_user_agents.utils import get_user_agent

try:
    from django.utils.deprecation import MiddlewareMixin
except: # noqa E722
    class MiddlewareMixin(object):
        pass


from pwdtk.auth_backends import PwdtkForceRenewException
from pwdtk.auth_backends import PwdtkLockedException
from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData
from pwdtk.views import lockout_response


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

    def must_renew_password(self, request):

        if request.method == 'GET':
            return False

        if not (request.user and request.user.is_authenticated):
            return False

        if not PwdData.get_or_create_for_user(request.user).must_renew:
            return False

        if request.path == reverse(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW):
            return False

        if request.path in PwdtkSettings.PWDTK_PASSWD_CHANGE_ALLOWED_PATHS:
            return False

        return True

    def process_exception(self, request, exception):

        if isinstance(exception, PwdtkLockedException):
            context = exception.pwdtk_data.get_lockout_context()
            if get_user_agent(request).is_mobile:
                return HttpResponse(
                    json.dumps(context),
                    content_type='application/json',
                    status=403,
                    )

            if PwdtkSettings.PWDTK_LOCKOUT_VIEW:
                return redirect("%s?%s" % (
                    reverse(PwdtkSettings.PWDTK_LOCKOUT_VIEW),
                    urlencode(context)
                    )
                )
            return lockout_response(request, exception.pwdtk_data)

        if isinstance(exception, PwdtkForceRenewException):
            return HttpResponse(
                json.dumps({"status": "PWDTK_NEED_RENEW_PASSWORD"}),
                content_type='application/json',
                status=403,
                )

        return None

    def process_request(self, request):

        if self.must_renew_password(request):
            if get_user_agent(request).is_mobile:
                return HttpResponse(
                    json.dumps({"status": "PWDTK_NEED_RENEW_PASSWORD"}),
                    content_type='application/json',
                    status=403,
                    )

            return redirect(reverse(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW))

    def process_response(self, request, response):

        if self.must_renew_password(request):
            if get_user_agent(request).is_mobile:
                return HttpResponse(
                    json.dumps({"status": "PWDTK_NEED_RENEW_PASSWORD"}),
                    content_type='application/json',
                    status=403,
                    )
            return redirect(reverse(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW))

        return response
