import logging

import django
from django import forms
from django import template

from django.contrib.auth import authenticate
import django.contrib.auth as auth
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.forms.widgets import PasswordInput
from django.http import HttpResponse
from django.shortcuts import render


logger = logging.getLogger(__name__)

HOME_TEMPLATE = """
welcome to the test space &lt;{{ username }}&gt;<br/>
You are {% if not username %} NOT {% endif %} logged in.<br/>
<br/>
<a href="/protected">Access the protected space</a><br/>
<a href="/admin">admin area</a><br/>
<a href="/login?next=/">Login</a><br/>
<a href="/logout?next=/">Logout</a><br/>
"""

LOGOUT_TEMPLATE = """
You should be logged out ({{ username }}).&gt;<br/>
You are {% if not username %} NOT {% endif %} logged in.<br/>
<br/>
<a href="/">Home</a><br/>
"""

PROTECTED_TEMPLATE = """
Welcome to the protected space.<br/>
You are {{ username }}
This space requires to be authenticated<br/>
<a href="/">Top</a><br/>
<a href="/admin/password_change/">Change password</a><br/>
<a href="/logout?next=/protected">Logout</a><br/>
"""


class LoginForm(forms.Form):
    username = forms.CharField(label='username', max_length=256)
    password = forms.CharField(label='password', max_length=256,
                               widget=PasswordInput)


def myauthenticate(request, **kwargs):
    if django.VERSION < (1, 9):
        return authenticate(**kwargs)
    else:
        return authenticate(request, **kwargs)


def home(request):
    """ a small home page for debugging / testing """
    tmplt = template.Template(HOME_TEMPLATE)
    ctx = template.Context(dict(
        username=request.user.username if request.user else "?",
        ))
    rendered = tmplt.render(ctx)
    return HttpResponse(rendered)


def login_view(request):
    ctx = dict(
        loggedin=False,
        )
    if request.method == 'POST':
        form = LoginForm(request.POST)
        logger.debug("handle login post request")
        if form.is_valid():
            logger.debug("form is valid")
            data = form.cleaned_data
            logger.debug("Data %s", data)
            username = data['username']
            password = data['password']
            user = myauthenticate(request, username=username,
                                  password=password)
            if user is not None:
                logger.debug("pwd OK for %s. will login", user.username)
                auth.login(request, user)
                ctx['loggedin'] = True
                ctx['username'] = user.username
            else:
                logger.debug("login error")
    else:
        logger.debug("should show login form")
        form = LoginForm()
    ctx['form'] = form
    return render(request, 'test/login.html', ctx)


@login_required
def logout_view(request):
    """ a small logout page for debugging / testing """
    user = request.user

    logout(request)
    logger.debug("user %s should be logged out now", user.username)
    tmplt = template.Template(LOGOUT_TEMPLATE)
    ctx = template.Context(dict(
        username=request.user.username if request.user else "?",
        ))
    rendered = tmplt.render(ctx)
    return HttpResponse(rendered)


@login_required
def protected(request):
    """ a small page for debugging / testing, that requires authentication """
    tmplt = template.Template(PROTECTED_TEMPLATE)
    ctx = template.Context(dict(
        username=request.user.username if request.user else "?",
        ))
    rendered = tmplt.render(ctx)
    return HttpResponse(rendered)
