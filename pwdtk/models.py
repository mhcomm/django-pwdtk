from __future__ import absolute_import

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
    user = models.OneToOneField(AUTH_USER_MODEL,
                                related_name='pwdtk_data',
                                on_delete=models.CASCADE, null=True)
    fake_username = models.CharField(max_length=150, unique=True, null=True)
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
            cls.objects.filter(fake_username=user.username).delete()

        return user.pwdtk_data

    def __str__(self):
        return("%r, %r" % ((self.user.id, self.user.username) if self.user else ("-", self.fake_username)))

    def set_locked(self, failed_logins=None):
        if failed_logins is not None:
            self.failed_logins = failed_logins
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
    def aware_fail_time(self):
        if timezone.is_aware(self.fail_time):
            return self.fail_time
        else:
            return pytz.timezone(
                PwdtkSettings.TIME_ZONE).localize(self.fail_time)

    @property
    def fail_age(self):

        return int((timezone.now() - self.fail_time).total_seconds())

    def compute_must_renew(self):
        """ determines whether a user must renew his password
        """
        if getattr(self.user, "disable_must_renew", False):
            return False
        if PwdtkSettings.PWDTK_PASSWD_AGE == 0:
            return False
        return ((timezone.now() - self.last_change_time).total_seconds() >
                PwdtkSettings.PWDTK_PASSWD_AGE)

    def get_lockout_context(self):
        return {
            "username": self.user.username if self.user else self.fake_username,
            "lockout_time": PwdtkSettings.PWDTK_LOCKOUT_TIME,
            "failed_logins": self.failed_logins,
            "fail_time": (
                        self.aware_fail_time.isoformat()
                        if self.fail_time else None
                    ),
        }
