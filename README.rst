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
