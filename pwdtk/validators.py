from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from django.db import transaction
import re

from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData
from pwdtk.signals import pwd_data_post_change_password


class PasswordHistoryValidator:
    """
    Validator for checking and maintaining user password history.
    """

    def __init__(self, history_length=None, error_messages=None):
        """Initialize validator with history length and custom error messages.

        Args:
            history_length (int, optional): Number of passwords to track.
                Defaults to PWDTK_PASSWD_HISTORY_LEN from settings.
            error_messages (dict, optional): Custom error messages to override defaults.
                Supported keys: 'password_reuse'
        """
        self.history_length = (
            history_length if history_length is not None
            else PwdtkSettings.PWDTK_PASSWD_HISTORY_LEN
        )

        self.error_messages = {
            'password_reuse': _(
                "Your password cannot be the same as any of your last %(history_length)d passwords."
            ),
        }

        if error_messages:
            self.error_messages.update(error_messages)

    def validate(self, password, user=None):
        """Check if password was previously used.

        Args:
            password (str): Password to validate.
            user (User, optional): User object to check history for.

        Raises:
            ValidationError: If password matches one in history.
        """
        if not user or not hasattr(user, 'pwdtk_data'):
            return
        for timestamp, old_hash in user.pwdtk_data.password_history:
            if check_password(password, old_hash):
                error_message = self.error_messages['password_reuse']
                if '%(history_length)d' in error_message:
                    error_message = error_message % {'history_length': self.history_length}
                raise ValidationError(
                    error_message,
                    code='password_history',
                )

    def password_changed(self, password, user=None):
        """Update password history after a successful change.

        Args:
            password (str): New password (unused but kept for API consistency).
            user (User, optional): User whose password changed.

        Note:
            Should only be called after new password is successfully set.
            Updates:
            - password_history (adds current password)

        Returns:
            PwdData: The updated user password data object
        """
        if not user:
            return None

        if not hasattr(user, 'pwdtk_data'):
            pwdtk_data = PwdData.get_or_create_for_user(user)
        else:
            pwdtk_data = user.pwdtk_data

        now = timezone.now()
        current_hash = user.password

        if not pwdtk_data.password_history or \
           pwdtk_data.password_history[0][1] != current_hash:
            with transaction.atomic():
                pwdtk_data.refresh_from_db(fields=['password_history'])
                pwdtk_data.password_history.insert(
                    0, (now.isoformat(), current_hash)
                )
                if len(pwdtk_data.password_history) > self.history_length:
                    pwdtk_data.password_history = \
                        pwdtk_data.password_history[:self.history_length]
                pwdtk_data.save(update_fields=['password_history'])
                pwd_data_post_change_password.send(
                    sender=self.__class__,
                    pwd_data=pwdtk_data
                )
        return pwdtk_data

    def get_help_text(self):
        """Return help text for password history requirements.
        """
        return _(
            "Your password cannot be the same as any of your last "
            "%(history_length)d passwords."
        ) % {'history_length': self.history_length}


class RegexPasswordValidator:
    """
    Validator for checking that a password matches a regex pattern.
    """

    def __init__(self, pattern=None, pattern_info=None, error_messages=None):
        """Initialize validator with regex pattern and custom error messages.

        Args:
            pattern (str, optional): Regex pattern passwords must match.
                Defaults to PWDTK_PASSWORD_ALLOWED_PATTERN from pwdtk settings.
            pattern_info (str, optional): Human-readable explanation of pattern.
                Defaults to PWDTK_PASSWORD_DEFAULT_PATTERN_INFO from pwdtk settings.
            error_messages (dict, optional): Custom error messages to override defaults.
        """
        self.pattern = (
            pattern if pattern is not None
            else getattr(PwdtkSettings, 'PWDTK_PASSWORD_ALLOWED_PATTERN', '')
        )

        self.pattern_info = (
            pattern_info if pattern_info is not None
            else getattr(PwdtkSettings, 'PWDTK_PASSWORD_DEFAULT_PATTERN_INFO', '')
        )

        self.error_messages = {
            'password_regex': _(
                "Password does not meet the required pattern. %(pattern_info)s"
            ),
        }

        if error_messages:
            self.error_messages.update(error_messages)

    def validate(self, password, user=None):
        """Check if password matches the required regex pattern.

        Args:
            password (str): Password to validate.
            user (User, optional): User object (unused but kept for API consistency).

        Raises:
            ValidationError: If password doesn't match the pattern.
        """
        if not self.pattern:
            return

        if not re.match(self.pattern, password):
            raise ValidationError(
                self.error_messages['password_regex'],
                code='password_regex',
                params={'pattern_info': self.pattern_info},
            )

    def get_help_text(self):
        """Return help text for password pattern requirements.

        Returns:
            str: Localized help text describing password pattern constraints
        """
        return self.pattern_info if self.pattern_info else _(
            "Your password must match the required pattern."
        )


class PasswordAgeValidator:
    """
    Validator responsible for updating password age metadata.
    """
    def __init__(self, max_age=None, error_messages=None):
        """Initialize validator with max password age.

        Args:
            max_age (int, optional): Max age in seconds.
                Defaults to PWDTK_PASSWD_AGE from settings.
            error_messages (dict, optional): Custom error messages.
                Supported keys: 'password_not_changed'
        """
        self.max_age = (
            max_age if max_age is not None
            else PwdtkSettings.PWDTK_PASSWD_AGE
        )
        self.error_messages = {
            'password_not_changed': _(
                "Your new password cannot be the same as your current password."
            ),
        }
        if error_messages:
            self.error_messages.update(error_messages)

    def validate(self, password, user=None):
        """Check if password actually changed.

        Args:
            password (str): Password to validate.
            user (User, optional): User object.

        Raises:
            ValidationError: If the password was not modified.
        """
        if user and user.check_password(password):
            raise ValidationError(
                self.error_messages['password_not_changed'],
                code='password_not_changed',
            )

    def password_changed(self, password, user=None):
        """Update password age metadata after a successful change.

        Args:
            password (str): New password (unused).
            user (User, optional): User whose password changed.

        Note:
            Should only be called after new password is successfully set.
            Updates:
            - last_change_time (sets to current time)
            - must_renew (sets to False)

        Returns:
            PwdData: The updated user password data object (or None)
        """
        if not user:
            return None

        if not hasattr(user, 'pwdtk_data'):
            pwdtk_data = PwdData.get_or_create_for_user(user)
        else:
            pwdtk_data = user.pwdtk_data

        now = timezone.now()

        with transaction.atomic():
            pwdtk_data.refresh_from_db(fields=['last_change_time', 'must_renew'])
            pwdtk_data.last_change_time = now.isoformat()
            pwdtk_data.must_renew = False
            pwdtk_data.save(update_fields=['last_change_time', 'must_renew'])

        return pwdtk_data

    def get_help_text(self):
        """Return help text for password age requirements.
        """
        return _("Your new password cannot be the same as your current password.")
