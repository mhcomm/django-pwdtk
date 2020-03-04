from __future__ import absolute_import

import datetime
import jsonfield

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from pwdtk.helpers import PwdtkSettings

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

@python_2_unicode_compatible
class PwdData(models.Model):
    """ a model in case no custom way is specified for storing related data
    """
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='pwdtk_data')
    locked = models.BooleanField(default=False)
    failed_logins = models.PositiveIntegerField(default=0)
    fail_time = models.DateTimeField(null=True)
    last_change_time = models.DateTimeField(default=datetime.datetime.utcnow)
    password_history = jsonfield.JSONField(default=[])

    def __str__(self):
        return("%r, %r" % (self.user.id, self.user.username))

    def is_locked(self):
        """ determines whether a user is still locked out
        """
        if not self.locked:
            return False
        if (datetime.datetime.utcnow() - self.fail_time).total_seconds() < PwdtkSettings.PWDTK_LOCKOUT_TIME:
            return True
        self.locked = False
        self.save()
        return False

    def must_renew(self):
        """ determines whether a user must renew his password
        """
        return (datetime.datetime.utcnow() - self.last_change_time).total_seconds() > PwdtkSettings.PWDTK_PASSWD_AGE
