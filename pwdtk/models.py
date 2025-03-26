from __future__ import absolute_import

import django
from django.conf import settings
from django.db import models
from django.utils import timezone

from pwdtk.helpers import PwdtkSettings

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def json_field(**kwargs):
    """
    Backward-compatible JSONField
    """
    if django.VERSION < (4, ):
        from django_jsonfield_backport.models import JSONField
        return JSONField(**kwargs)
    else:
        from django.db.models import JSONField
        return JSONField(**kwargs)


class PwdData(models.Model):
    """ a model in case no custom way is specified for storing related data
    """
    user = models.OneToOneField(AUTH_USER_MODEL,
                                related_name='pwdtk_data',
                                on_delete=models.CASCADE, null=True)
    fake_username = models.CharField(max_length=150, unique=True, null=True)
    locked = models.BooleanField(default=False)
    failed_logins = models.PositiveIntegerField(default=0)
    lockout_count = models.PositiveIntegerField(default=0)
    fail_time = models.DateTimeField(null=True)
    must_renew = models.BooleanField(default=False)
    last_change_time = models.DateTimeField(default=timezone.now)
    password_history = json_field(default=[])

    @classmethod
    def get_or_create_for_user(cls, user):
        if not hasattr(user, 'pwdtk_data'):
            user.pwdtk_data = cls.objects.create(user=user)
            cls.objects.filter(fake_username=user.username).delete()

        return user.pwdtk_data

    def __str__(self):
        return ("%r, %r" % ((self.user.id, self.user.username) if self.user else ("-", self.fake_username)))

    def set_locked(self, failed_logins=None):
        if failed_logins is not None:
            self.failed_logins = failed_logins
        self.locked = True
        self.fail_time = timezone.now()
        self.lockout_count += 1
        self.save()

    def calculate_current_lockout_time(self):
        """Calculate the current lockout time based on the lockout count."""
        lockout_multiplier = getattr(PwdtkSettings, 'PWDTK_LOCKOUT_MULTIPLIER', 1)
        current_lockout_time = PwdtkSettings.PWDTK_LOCKOUT_TIME
        if self.lockout_count > 0:
            current_lockout_time = PwdtkSettings.PWDTK_LOCKOUT_TIME * (lockout_multiplier ** (self.lockout_count - 1))
        return current_lockout_time

    def is_locked(self):
        """ determines whether a user is still locked out
        """
        if not self.locked:
            return False

        current_lockout_time = self.calculate_current_lockout_time()

        if self.fail_age < current_lockout_time:
            return True

        self.locked = False
        self.failed_logins = 0
        self.save()
        return False

    @property
    def aware_fail_time(self):
        if timezone.is_aware(self.fail_time):
            return self.fail_time
        else:
            if django.VERSION < (4, 0):
                import pytz
                return pytz.timezone(
                    PwdtkSettings.TIME_ZONE).localize(self.fail_time)
            else:
                from zoneinfo import ZoneInfo
                return self.fail_time.replace(
                    tzinfo=ZoneInfo(PwdtkSettings.TIME_ZONE))

    @property
    def fail_age(self):
        return int((timezone.now() - self.fail_time).total_seconds())

    @property
    def lockout_time_remaining(self):
        """Return the remaining lockout time in seconds, or 0 if not locked."""
        if not self.locked or not self.fail_time:
            return 0

        current_lockout_time = self.calculate_current_lockout_time()

        remaining = current_lockout_time - self.fail_age
        return max(0, remaining)

    @property
    def lockout_time_remaining_formatted(self):
        """Return the remaining lockout time as a human-readable string."""
        seconds = self.lockout_time_remaining
        if seconds <= 0:
            return "Not locked"

        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

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
        current_lockout_time = self.calculate_current_lockout_time()
        return {
            "username": self.user.username if self.user else self.fake_username,
            "lockout_time": current_lockout_time,
            "failed_logins": self.failed_logins,
            "fail_time": (
                        self.aware_fail_time.isoformat()
                        if self.fail_time else None
                    ),
            "lockout_count": self.lockout_count,
        }
