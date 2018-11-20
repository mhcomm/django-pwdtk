from __future__ import absolute_import
from __future__ import print_function

import logging

# import django

from django.contrib.auth.signals import user_logged_in
# from django.contrib.auth.signals import user_logged_out
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

from pwdtk.auth_backends import MHPwdPolicyBackend
from pwdtk.auth_backends import PwdTkMustChangePassword


logger = logging.getLogger(__name__)
logger.debug("Imp backend2 sigs")  # for debugging dj 1.8 -> 1.11

NOT_SET = object()

get_backend = MHPwdPolicyBackend.get_backend


@receiver(user_login_failed)
def handle_loginfailed(sender, credentials, **kwargs):
    logger.debug(
        "handle login_failed_sig %s %s %s",
        repr(sender), repr(credentials), repr(kwargs))
    if not isinstance(credentials, dict) or 'username' not in credentials:
        return
    request = kwargs['request'] if 'request' in kwargs else None
    username = credentials['username']
    logger.debug("LOGIN_FAILED for %s %s", username, repr(kwargs))
    get_backend().handle_failed_login(username, request)


@receiver(user_logged_in)
def handle_login(sender, **kwargs):
    logger.debug("Handle logged_in sig %s %s", repr(sender), repr(kwargs))
    if 'request' not in kwargs:
        return
    user = getattr(kwargs['request'], 'user',  NOT_SET)
    if user is NOT_SET:
        logger.debug("login without username")
        return
    username = user.username
    logger.debug("LOGIN as %s", username)
    backend = get_backend()
    backend.clear_failed_logins(user=user)
    logger.debug("check for old passwd")
    try:
        backend.check_obsolete_passwords(username)
    except PwdTkMustChangePassword:
        request = kwargs['request'] if 'request' in kwargs else None
        logger.debug("change pwd (req = %s)", repr(request))
        request.pwdtk_fail_user = username
        request.pwdtk_fail_reason = 'pwd_obsolete'


# @receiver(user_logged_out)
# def handle_logout(sender, **kwargs):
#     print("LOGOUT", kwargs)
