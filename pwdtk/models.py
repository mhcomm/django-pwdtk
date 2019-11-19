from __future__ import absolute_import


import jsonfield

from django.conf import settings
from django.db import models

from pwdtk.helpers import get_delta_seconds


class PwdData(models.Model):
    """ a model in case no custom way is specified for storing related data
    """
    user_id = models.PositiveIntegerField(null=True, blank=True, default=0)
    username = models.CharField(max_length=255, null=True,
                                unique=True)
    data = jsonfield.JSONField(default={})

    def __unicode__(self):
        return("%r, %r" % (self.user_id, self.username))

    def locked_out(self):
        """ whether user is locked out or not """
        data = self.data
        locked = data.get('locked')
        fail_age = get_delta_seconds(data.get('fail_time'))
        if locked:
            if fail_age < settings.PWDTK_LOCKOUT_TIME:
                return True
        return False

    def lockout_info(self):
        """ info about being locked out due to password failures """
        data = self.data
        locked = data.get('locked')
        fail_age = get_delta_seconds(data.get('fail_time'))
        if locked:
            if fail_age < settings.PWDTK_LOCKOUT_TIME:
                return 'true (%s) %ss' % (
                    data.get('failed_logins', '?'), fail_age)
        return 'false (%s)' % data.get('failed_logins', '?')

    def must_renew(self):
        """ must the password be renewed """
        history = self.data.get('passwd_history')
        if not history:
            return False
        change_delta = get_delta_seconds(history[0][0])
        return change_delta > settings.PWDTK_PASSWD_AGE
