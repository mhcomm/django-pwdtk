PWDTK Password Tool Kit for Django
====================================

.. image:: https://api.travis-ci.com/mhcomm/django-pwdtk.svg?branch=master
    :target: https://travis-ci.com/mhcomm/django-pwdtk


You use Django's default password authentification, but miss some tweaks
like:
* lockout after too many failed logins
* max life time for passwords
* password reset (send mail with reset link) (not implemented so far)
* password history validation
* regex pattern validation for passwords

This package provides solutions for these problems.
PWDTK is compatible with python 2.7, and >=3.5
It is compatible with django 2.2, 3.2 and 4.2

Password Pattern Validation
--------------------------

PWDTK supports regex-based password validation to enforce password complexity rules. 
To use this feature, add the RegexPasswordValidator to your settings:

.. code-block:: python

    # In your settings.py
    
    # Set the regex pattern that passwords must match
    PWDTK_PASSWORD_ALLOWED_PATTERN = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
    
    # Set a human-readable explanation of the pattern
    PWDTK_PASSWORD_DEFAULT_PATTERN_INFO = "Password must be at least 8 characters and include both letters and numbers."
    
    # Use both history and regex validators
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'pwdtk.validators.PasswordHistoryValidator',
        },
        {
            'NAME': 'pwdtk.validators.RegexPasswordValidator',
        },
    ]

The example above requires passwords to:
- Be at least 8 characters long
- Contain at least one letter and one number

Forced Password Renewal
--------------------------

PWDTK can demand the renewal of the password of a user. Such a user cannot log
in anymore: the authentication backend raises a ``PwdtkForceRenewException``,
which the PWDTK middleware turns into a 403 response holding
``{"status": "PWDTK_NEED_RENEW_PASSWORD"}``. It is up to the integrating tool
to lead the user to a password change form.

Three modes demand a renewal. They are independent and can be combined:

**1. The password is too old.** The PasswordAgeValidator demands a renewal
once the password is older than its ``max_age``, in seconds, which defaults to
the ``PWDTK_PASSWD_AGE`` setting (30 days). Beware that this mode is disabled
when ``max_age`` is 0, the validator keeping all its other effects. When
several PasswordAgeValidator are active, the smallest ``max_age`` wins, hence
a single one set to 0 disables the mode altogether.

**2. The user logs in for the first time.** With
``PWDTK_FORCE_RENEW_ON_FIRST_LOGIN`` every new user has to renew his password
at his very first login attempt.

**3. The integrating tool demands it.** ``PwdData.force_renew()`` demands the
renewal of the password of a given user at his next login.

The modes 2 and 3 set the ``must_renew`` flag of the pwdtk data of the user.
The mode 1 is evaluated at each login attempt and its result is stored in that
same flag. Whatever the mode, a truthy ``disable_must_renew`` attribute on the
user object exempts him from any renewal.

All three modes need an active PasswordAgeValidator, as its
``password_changed`` hook is the only one resetting ``must_renew`` and
refreshing the age of the password. Without it a user demanded to renew his
password would never be able to log in again. Note that the validator is
needed for its reset even when ``max_age`` is 0, which is how a renewal is
demanded on the first login without expiring the passwords afterwards:

.. code-block:: python

    # In your settings.py

    # Demand a renewal at the first login of every new user
    PWDTK_FORCE_RENEW_ON_FIRST_LOGIN = True

    # Do not demand any renewal because of the age of the passwords
    PWDTK_PASSWD_AGE = 0

    AUTH_PASSWORD_VALIDATORS = [
        {
            # still required to reset must_renew on a password change
            'NAME': 'pwdtk.validators.PasswordAgeValidator',
        },
    ]

A missing PasswordAgeValidator is reported by the ``pwdtk.W001`` system check
when ``PWDTK_FORCE_RENEW_ON_FIRST_LOGIN`` is enabled, and by a
``PwdtkConfigWarning`` when ``force_renew()`` is called.

Password History Validation
--------------------------

PWDTK prevents users from reusing their previous passwords. This feature helps maintain security by ensuring users don't cycle through a small set of passwords.

To configure password history validation, add the following to your settings:

.. code-block:: python

    # In your settings.py
    
    # Set the number of previous passwords to remember
    PWDTK_PASSWD_HISTORY_LEN = 3
    
    # Add the validator to your AUTH_PASSWORD_VALIDATORS
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'pwdtk.validators.PasswordHistoryValidator',
        },
    ]

With this configuration:
- Users cannot reuse any of their last 3 passwords
- Each time a user changes their password, the system stores the password hash
- When a user attempts to set a new password, it's checked against their password history
