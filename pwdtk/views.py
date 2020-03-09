import logging

from django.http import HttpResponse
from django.shortcuts import render


from pwdtk.helpers import PwdtkSettings

logger = logging.getLogger(__name__)


def lockout_response(request, context):
    """ create login response for locked out users
    """
    if request.is_ajax():
        return HttpResponse(
            json.dumps(context),
            content_type='application/json',
            status=403,
        )

    return render(request, PwdtkSettings.PWDTK_LOCKOUT_TEMPLATE, context, status=403)
