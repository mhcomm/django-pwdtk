from __future__ import absolute_import


class PwdTkBackendError(Exception):
    """ custom exception """


class PwdTkMustChangePassword(Exception):
    """ whenever a user must change his password """
