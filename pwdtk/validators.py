from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from django.db import transaction

from pwdtk.helpers import PwdtkSettings
from pwdtk.models import PwdData


class PasswordHistoryValidator:
    """Validator for checking and maintaining user password history."""

    def __init__(self, history_length=None):
        """Initialize validator with history length.

        Args:
            history_length (int, optional): Number of passwords to track.
                Defaults to PWDTK_PASSWD_HISTORY_LEN from settings.
        """
        self.history_length = (
            history_length if history_length is not None
            else PwdtkSettings.PWDTK_PASSWD_HISTORY_LEN
        )

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
        for _timestamp, old_hash in user.pwdtk_data.password_history:
            if check_password(password, old_hash):
                raise ValidationError(
                    _(
                        "Password was used previously. You must wait for "
                        "%(history_length)d password changes before reusing "
                        "an old password."
                    ),
                    code='password_history',
                    params={'history_length': self.history_length},
                )
    
    def password_changed(self, password, user=None):
        """Update password history after a successful change.

        Args:
            password (str): New password (unused but kept for API consistency).
            user (User, optional): User whose password changed.

        Note:
            Should only be called after new password is successfully set.
        """
        if not user or not hasattr(user, 'pwdtk_data'):
            pwdtk_data = PwdData.get_or_create_for_user(user)
        else:
            pwdtk_data = user.pwdtk_data
        now = timezone.now()
        current_hash = user.password
        if not pwdtk_data.password_history or \
           pwdtk_data.password_history[0][1] != current_hash:
            with transaction.atomic():
                pwdtk_data.refresh_from_db()
                pwdtk_data.password_history.insert(
                    0, (now.isoformat(), current_hash)
                )
                if len(pwdtk_data.password_history) > self.history_length:
                    pwdtk_data.password_history = \
                        pwdtk_data.password_history[:self.history_length]
                pwdtk_data.save()

    def get_help_text(self):
        """Return help text for password history requirements."""
        return _(
            "Your password cannot be the same as any of your last "
            "%(history_length)d passwords."
        ) % {'history_length': self.history_length}
