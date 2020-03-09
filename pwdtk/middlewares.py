import datetime
import json
import logging

from six.moves.urllib.parse import urlencode


from django.core.exceptions import MiddlewareNotUsed
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect


from pwdtk.views import lockout_response
from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData


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
        logger.debug("PWDTK Proc Req %s %s", request.user, repr(request))
        request.pwdtk_fail_user = None
        request.pwdtk_fail_reason = None


    def process_request(self, request):

        if (request.method != 'GET' and request.user.is_authenticated()
          and PwdData.get_or_create_for_user(request.user).must_renew):
            if (request.path != reverse(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW) and
              request.path not in PwdtkSettings.PWDTK_PASSWD_CHANGE_ALLOWED_PATHS):
                return redirect(reverse(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW))

    def process_response(self, request, response):

        if (request.method != 'GET' and request.user.is_authenticated() and
          PwdData.get_or_create_for_user(request.user).must_renew and
          request.path not in PwdtkSettings.PWDTK_PASSWD_CHANGE_ALLOWED_PATHS):
            if request.path != reverse(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW):
                return redirect(reverse(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW))

        if getattr(request, "pwdtk_fail", None):
            fail_reason = request.pwdtk_fail_reason
            context = {
                'username': request.pwdtk_user.user.username,
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
            next = request.POST.get('next')
            if fail_reason == "lockout":
                if PwdtkSettings.PWDTK_LOCKOUT_VIEW:
                    context = request.pwdtk_user.get_lockout_context()
                    if next:
                        context["next"] = next
                    return redirect("%s?%s" % (reverse(PwdtkSettings.PWDTK_LOCKOUT_VIEW), urlencode(context)))

                context.update(self.handle_lockout_context(request.pwdtk_user))
                return lockout_response(request, context)

            if fail_reason == "pwd_obsolete":
                return redirect(reverse(PwdtkSettings.PWDTK_PASSWD_CHANGE_VIEW))

        return response
