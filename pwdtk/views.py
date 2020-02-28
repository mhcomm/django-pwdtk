import logging

import datetime
import dateutil.parser


from django.http import HttpResponse
from django.shortcuts import render


from pwdtk.helpers import PwdtkSettings
from pwdtk.helpers import seconds_to_iso8601

logger = logging.getLogger(__name__)


def lockout_response(request, pwdtk_user_data, msg=''):
    """ create login response for locked out users
    """
    # username = request.POST.get(PwdtkSettings.PWDTK_USERNAME_FORM_FIELD, '')
    context = {
        'failure_limit': pwdtk_user_data.failed_logins,
        'username': pwdtk_user_data.username,
        'msg': msg,
    }

    if PwdtkSettings.PWDTK_LOCKOUT_TIME:
        context.update({'cooloff_time':
                       seconds_to_iso8601(PwdtkSettings.PWDTK_LOCKOUT_TIME)})

    user_data = pwdtk_user_data
    t_fail = dateutil.parser.parse(user_data.fail_time)
    t_delta = datetime.datetime.utcnow() - t_fail
    age = t_delta.days * 86400 + t_delta.seconds
    to_wait = PwdtkSettings.PWDTK_LOCKOUT_TIME - age
    to_wait_minutes, to_wait_seconds = divmod(to_wait, 60)
    to_wait_str = "%d minutes and %d seconds" % (
        to_wait_minutes, to_wait_seconds)
    context['to_wait'] = to_wait_str
    context['to_wait_time_tuple'] = (to_wait_minutes, to_wait_seconds)

    logger.debug("CTX: %s", context)

    if request.is_ajax():
        return HttpResponse(
            json.dumps(context),
            content_type='application/json',
            status=403,
        )
    if PwdtkSettings.PWDTK_LOCKOUT_TEMPLATE:
        return render(request, PwdtkSettings.PWDTK_LOCKOUT_TEMPLATE, context, status=403)
