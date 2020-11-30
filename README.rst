PWDTK Password Tool Kit for Django
====================================

.. image:: https://api.travis-ci.com/mhcomm/django-pwdtk.svg?branch=master
    :target: https://travis-ci.com/mhcomm/django-pwdtk


You use Django's default password authentification, but miss some tweaks
like:
* lockout after too many failed logins
* max life time for passwords
* password reset (send mail with reset link) (not implemented so far)

This package provides solutions for these problems.
PWDTK is compatible with python 2.7, and >=3.5
It is compatible with django 1.11, 2.2
