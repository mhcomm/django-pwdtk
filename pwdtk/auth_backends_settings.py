import django


def add_backend(backends):
    """ adds auth backend depending on django version
    """
    if django.VERSION >= (2, ):
        backends.insert(
            0, 'pwdtk.auth_backends.MHPwdPolicyBackend')


PWDTK_USER_PARAMS = 'pwdtk.auth_backends_data.UserData'
PWDTK_LOCKOUT_TIME = 60
PWDTK_USER_FAILURE_LIMIT = 3
PWDTK_USERNAME_FORM_FIELD = 'username'
PWDTK_IP_FAILURE_LIMIT = 0
PWDTK_LOCKOUT_TEMPLATE = 'login/locked_out_simple.html'
