import django


def add_backend(backends):
    """ adds auth backend depending on django version
    """
    if django.VERSION >= (1, 11):
        backends.insert(
            0, 'pwdtk.auth_backends.MHPwdPolicyBackend')


def add_middlewares(
        middlewares,
        after='django.contrib.auth.middleware.AuthenticationMiddleware'):
    """ adds middlewares depending on django.VERSION """
    assert type(middlewares) is list
    idx = middlewares.index(after) + 1
    to_insert = []
    if django.VERSION >= (1, 11):
        to_insert.append('pwdtk.middlewares.PwdtkMiddleware')

    middlewares[idx:idx] = to_insert

# PWDTK Common settings for login / logout views
# ----------------------------------------------------------


# Model to be used for storing PWDTK related info
PWDTK_USER_PARAMS = 'pwdtk.auth_backends_data.UserData'

# to know what login views to watch
# for django < 1.11
PWDTK_LOGIN_VIEW = 'django.contrib.auth.views.login'

# for django > 1.11
PWDTK_LOGIN_VIEW_CLASS = 'django.contrib.auth.views.LoginView'


# PWDTK Passsword lockout after logins with bad password
# ----------------------------------------------------------


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
PWDTK_PASSWD_CHANGE_VIEW = "password_change"
PWDTK_PASSWD_CHANGE_TEMPLATE = "login/passwd_change_simple.html"


# for PWDTK unit testing.
# --------------------------

# Url of the admin page
PWDTK_TEST_ADMIN_URL = "/admin/"

# message to be found in contents to detect a bad login
PWDTK_TEST_LOGIN_FAIL_SUBMSG = b'Please enter the correct'

# message to be found in contents to detect a locked out user
PWDTK_TEST_LOCKOUT_SUBMSG = b'So bad!'
