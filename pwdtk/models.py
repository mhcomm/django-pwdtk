from __future__ import absolute_import

import datetime
import jsonfield
import pytz

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone

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
    must_renew = models.BooleanField(default=False)
    last_change_time = models.DateTimeField(default=timezone.now)
    password_history = jsonfield.JSONField(default=[])

    @classmethod
    def get_or_create_for_user(cls, user):
        if not hasattr(user, 'pwdtk_data'):
            user.pwdtk_data = cls.objects.create(user=user)
        return user.pwdtk_data

    def __str__(self):
        return("%r, %r" % (self.user.id, self.user.username))


    def set_locked(self):

        self.locked = True
        self.fail_time = timezone.now()
        self.save()

    def is_locked(self):
        """ determines whether a user is still locked out
        """
        if not self.locked:
            return False

        if self.fail_age < PwdtkSettings.PWDTK_LOCKOUT_TIME:
            return True

        self.locked = False
        self.save()
        return False

    @property
    def fail_age(self):

        return int((timezone.now() - self.fail_time).total_seconds())

    def compute_must_renew(self):
        """ determines whether a user must renew his password
        """

        return (timezone.now() - self.last_change_time).total_seconds() > PwdtkSettings.PWDTK_PASSWD_AGE

    def handle_lockout_context(self):

        age = self.fail_age
        to_wait = PwdtkSettings.PWDTK_LOCKOUT_TIME - age
        to_wait_minutes, to_wait_seconds = divmod(to_wait, 60)
        to_wait_str = "%i minutes and %i seconds" % (to_wait_minutes, to_wait_seconds)

        return {
            'to_wait': to_wait_str,
            'to_wait_time_tuple': (to_wait_minutes, to_wait_seconds),
            'failure_limit': self.failed_logins,

        }

    def get_lockout_context(self):
        if timezone.is_aware(self.fail_time):
            fail_time = self.fail_time.isoformat()
        else:
            fail_time = pytz.timezone(PwdtkSettings.TIME_ZONE).localize(self.fail_time).isoformat()
        return {
            "username": self.user.username,
            "lockout_time": PwdtkSettings.PWDTK_LOCKOUT_TIME,
            "failed_logins": self.failed_logins,
            "fail_time": fail_time,
        }
