import django


def add_backend(backends):
    """ adds auth backend depending on django version
    """
    if django.VERSION >= (2, ):
        backends.insert(
            0, 'pwdtk.auth_backends.MHPwdPolicyBackend')

# PWDTK Passsword lockout after logins with bad password
# ----------------------------------------------------------


# Model to be used for storing PWDTK related info
PWDTK_USER_PARAMS = 'pwdtk.auth_backends_data.UserData'

# Time in seconds to lockout a user who entered a bad password too iften
PWDTK_LOCKOUT_TIME = 60

# Amount of bad passwords before a user is locked out
PWDTK_USER_FAILURE_LIMIT = 3

# the field in the login form, that contains the user name
PWDTK_USERNAME_FORM_FIELD = 'username'

# the field in the login form, that contains the password
# PWDTK_PASSWORD_FORM_FIELD = 'username'

# Name of the template to be used when a user is locked out
PWDTK_LOCKOUT_TEMPLATE = 'login/locked_out_simple.html'

PWDTK_IP_FAILURE_LIMIT = 0


# PWDTK force password renewal
# ------------------------------
# should ckeck code of https://github.com/tarak/django-password-policies to
# see, that we use a similiar config.

# age of passwords before it has to be renewed
PWDTK_PASSWD_AGE = 30 * 24 * 60 * 60

# amount of passwords before and old password can be reused
PWDTK_PASSWD_HISTORY_LEN = 3

# template to display for password renewal
PWDTK_LOCKOUT_TEMPLATE = 'login/locked_out_simple.html'


# for PWDTK unit testing.
# --------------------------

# Url of the admin page
PWDTK_TEST_ADMIN_URL = "/admin/"

# message to be found in contents to detect a bad login
PWDTK_TEST_LOGIN_FAIL_SUBMSG = b'Please enter the correct'

# message to be found in contents to detect a locked out user
PWDTK_TEST_LOCKOUT_SUBMSG = b'So bad!'
