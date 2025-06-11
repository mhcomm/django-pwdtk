from __future__ import absolute_import

import sys

import django
from django.conf import settings
from django.contrib.auth.password_validation import get_default_password_validators
from django.db import models
from django.utils import timezone

from pwdtk.exceptions import PwdtkLockedException
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


def make_tz_aware(time):
    if time is None:
        return None
    if timezone.is_aware(time):
        return time
    else:
        if django.VERSION < (4, 0) or sys.version_info < (3, 9):
            import pytz
            return pytz.timezone(
                PwdtkSettings.TIME_ZONE).localize(time)
        else:
            from zoneinfo import ZoneInfo
            return time.replace(
                tzinfo=ZoneInfo(PwdtkSettings.TIME_ZONE))


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
    password_history = json_field(default=list)
    locked_until = models.DateTimeField(null=True)

    @classmethod
    def get_or_create_for_user(cls, user):
        if not hasattr(user, 'pwdtk_data'):
            user.pwdtk_data = cls.objects.create(user=user)
            cls.objects.filter(fake_username=user.username).delete()

        return user.pwdtk_data

    def __str__(self):
        return ("%r, %r" % ((self.user.id, self.user.username) if self.user else ("-", self.fake_username)))

    def register_failed_login(self):
        """Register a failed login.

        @raises PwdtkLockedException: the account is locked after the failed login.
        """
        user_failure_limit = PwdtkSettings.PWDTK_USER_FAILURE_LIMIT
        self.failed_logins += 1
        self.fail_time = timezone.now()
        if user_failure_limit and self.failed_logins >= user_failure_limit:
            self.set_locked()
            raise PwdtkLockedException(self)
        else:
            self.save()

    def set_locked(self):
        """Lock an account for a certain time."""
        self.locked = True
        lockout_multiplier = getattr(PwdtkSettings, 'PWDTK_LOCKOUT_MULTIPLIER', 1)
        current_lockout_time = PwdtkSettings.PWDTK_LOCKOUT_TIME
        max_lockout_time = PwdtkSettings.PWDTK_MAX_LOCKOUT_TIME
        user_failure_limit = PwdtkSettings.PWDTK_USER_FAILURE_LIMIT
        if self.failed_logins >= user_failure_limit:
            exponent = self.failed_logins - user_failure_limit
            current_lockout_time = PwdtkSettings.PWDTK_LOCKOUT_TIME * (lockout_multiplier ** exponent)
            if max_lockout_time > 0:
                current_lockout_time = min(current_lockout_time, max_lockout_time)
        self.locked_until = timezone.now() + timezone.timedelta(seconds=current_lockout_time)
        self.save()

    def is_locked(self):
        """ determines whether a user is still locked out
        """
        if not self.locked:
            return False

        if timezone.now() < self.locked_until:
            return True

        self.locked = False
        self.save()
        return False

    @property
    def aware_fail_time(self):
        return make_tz_aware(self.fail_time)

    @property
    def fail_age(self):
        return int((timezone.now() - self.fail_time).total_seconds())

    def compute_must_renew(self):
        """ determines whether a user must renew his password
        """
        from pwdtk.validators import PasswordAgeValidator
        if getattr(self.user, "disable_must_renew", False):
            return False
        if PwdtkSettings.PWDTK_PASSWD_AGE == 0:
            return False
        max_ages = [validator.max_age for validator in get_default_password_validators()
                    if isinstance(validator, PasswordAgeValidator)]
        if len(max_ages) == 0:
            return False
        password_max_age = min(max_ages)
        if password_max_age == 0:
            return False
        return ((timezone.now() - self.last_change_time).total_seconds() >
                password_max_age)

    def get_lockout_context(self):
        return {
            "username": self.user.username if self.user else self.fake_username,
            "failed_logins": self.failed_logins,
            "fail_time": (
                self.aware_fail_time.isoformat()
                if self.fail_time else None
            ),
            "locked_until": (
                make_tz_aware(self.locked_until).isoformat()
                if self.locked_until else None
            ),
        }
