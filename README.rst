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

Account Lockout
---------------

PWDTK locks an account out for a while after too many logins with a bad
password. Login attempts with a user name matching no user are counted and
locked out the same way.

.. code-block:: python

    # In your settings.py

    # Amount of logins with a bad password before a lockout (0 to disable)
    PWDTK_USER_FAILURE_LIMIT = 3

    # Duration of a first lockout, in seconds
    PWDTK_LOCKOUT_TIME = 60

    # Factor applied to the lockout time after each additional failed login
    PWDTK_LOCKOUT_MULTIPLIER = 2

    # Longest lockout, in seconds (0 for no limit)
    PWDTK_MAX_LOCKOUT_TIME = 24 * 60 * 60

With this configuration:

- The third login with a bad password locks the account for 60 seconds
- Each further login with a bad password multiplies the duration of the next
  lockout by 2 (120 seconds, 240 seconds, ...) up to one day
- A locked out user is refused, even when he finally uses his right password
- The failed logins are only forgotten by a successful login, hence a user
  who keeps failing right after each lockout is locked out longer and longer

A refused login raises a ``pwdtk.exceptions.PwdtkLockedException``, which
``pwdtk.middlewares.PwdtkMiddleware`` turns into a 403 response describing
the lockout:

.. code-block:: json

    {
        "status": "PWDTK_LOCKED",
        "username": "jdoe",
        "failed_logins": 3,
        "fail_time": "2024-01-01T10:00:00+00:00",
        "locked_until": "2024-01-01T10:01:00+00:00"
    }

An integrating tool can lift a lockout before its expiry:

.. code-block:: python

    from pwdtk.models import PwdData

    PwdData.get_or_create_for_user(user).unlock()

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
