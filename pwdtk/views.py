import logging

# from django.conf import settings

from django import forms

from django.forms.widgets import PasswordInput
from django.shortcuts import render


logger = logging.getLogger(__name__)


class PasswdChange(forms.Form):
    password = forms.CharField(label='password', max_length=256,
                               widget=PasswordInput)
    password2 = forms.CharField(label='confirm password', max_length=256,
                               widget=PasswordInput)


def password_change(request, username=""):
    user = request.user
    ctx = dict(
        username=user.username if user else "?",
        errormsg = "",
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
    return render(request, 'passwd_change_simple.html', ctx)
