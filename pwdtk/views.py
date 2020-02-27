import logging

# from django.conf import settings

from django import forms

from django.forms.widgets import PasswordInput
from django.shortcuts import render


from pwdtk.helpers import PwdtkSettings
from pwdtk.helpers import seconds_to_iso8601

logger = logging.getLogger(__name__)


class PasswdChange(forms.Form):
    password = forms.CharField(label='password', max_length=256, widget=PasswordInput)
    password2 = forms.CharField(label='confirm password', max_length=256, widget=PasswordInput)


def password_change(request, username=""):
    user = request.user
    ctx = dict(
        username=user.username if user else "?",
        errormsg="",
        )
    if request.method == 'POST':
        form = PasswdChange(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            logger.debug("form is valid")
            password = data['password']
            password2 = data['password2']
            if password != password2:
                ctx['errormsg'] = "both passwords must be identical"
            else:
                user.set_password(password)
                user.save()
    else:
        form = PasswdChange()
    ctx['form'] = form
    return render(request, 'login/passwd_change_simple.html', ctx)


def lockout_response(request, username, msg=''):
    """ create login response for locked out users
    """
    # username = request.POST.get(PwdtkSettings.PWDTK_USERNAME_FORM_FIELD, '')
    context = {
        'failure_limit': PwdtkSettings.PWDTK_USER_FAILURE_LIMIT,
        'username': username,
        'msg': msg,
    }

    if PwdtkSettings.PWDTK_LOCKOUT_TIME:
        context.update({'cooloff_time': seconds_to_iso8601(PwdtkSettings.PWDTK_LOCKOUT_TIME)})

        user_data = backend.userdata_cls(username=username)
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
