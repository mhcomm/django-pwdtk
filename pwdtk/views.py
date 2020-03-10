import logging

from dateutil.parser import parse

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone


from pwdtk.helpers import PwdtkSettings

logger = logging.getLogger(__name__)


def lockout_response(request, pwdtk_data):
    """ create login response for locked out users
    """

    age = pwdtk_data.fail_age
    to_wait = PwdtkSettings.PWDTK_LOCKOUT_TIME - age
    to_wait_minutes, to_wait_seconds = divmod(to_wait, 60)
    to_wait_str = "%i minutes and %i seconds" % (to_wait_minutes, to_wait_seconds)
    lockout_context = {
        "to_wait": to_wait_str,
        'failure_limit': pwdtk_data.failed_logins,
        'to_wait_time_tuple': (to_wait_minutes, to_wait_seconds),
    }


    return render(request, PwdtkSettings.PWDTK_LOCKOUT_TEMPLATE, lockout_context, status=403)
