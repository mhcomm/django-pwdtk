#!/usr/bin/env python

# ############################################################################
# Name       : pwdtk.exceptions
"""
  Summary    : pwdtk custom Exception classes
"""
# #############################################################################


class PwdtkBaseException(Exception):

    def __init__(self, pwdtk_data):

        self.pwdtk_data = pwdtk_data


class PwdtkLockedException(PwdtkBaseException):
    """ custom exception """


class PwdtkForceRenewException(PwdtkBaseException):
    """ custom exception """
