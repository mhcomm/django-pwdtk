#!/usr/bin/env python

# ############################################################################
# Name       : pwdtk.checks
"""
  Summary    : pwdtk django system checks
"""
# #############################################################################

from django.core.checks import Warning


PASSWORD_AGE_VALIDATOR = 'pwdtk.validators.PasswordAgeValidator'


def check_force_renew_on_first_login(app_configs, **kwargs):
    """Check that a renewal forced on first login can be lifted.

    Note:
        PWDTK_FORCE_RENEW_ON_FIRST_LOGIN sets must_renew for every new user
        and only the PasswordAgeValidator resets it, so without that
        validator no user would ever be able to log in.

    Returns:
        list: the detected configuration warnings
    """
    from pwdtk.helpers import PwdtkSettings
    from pwdtk.validators import get_password_age_validators

    if not PwdtkSettings.PWDTK_ENABLED:
        return []

    if not PwdtkSettings.PWDTK_FORCE_RENEW_ON_FIRST_LOGIN:
        return []

    if get_password_age_validators():
        return []

    return [
        Warning(
            "PWDTK_FORCE_RENEW_ON_FIRST_LOGIN is enabled but %s is missing "
            "from AUTH_PASSWORD_VALIDATORS." % PASSWORD_AGE_VALIDATOR,
            hint="%s is the only validator resetting must_renew. Without it "
                 "the users forced to renew their password on their first "
                 "login will never be able to log in." % PASSWORD_AGE_VALIDATOR,
            id='pwdtk.W001',
            )
        ]
