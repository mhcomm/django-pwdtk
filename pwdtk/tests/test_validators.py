import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from pwdtk.validators import RegexPasswordValidator, PasswordHistoryValidator, PasswordAgeValidator
from pwdtk.models import PwdData


# -------------------- Password History Validator -----------

class PasswordHistoryValidatorTest(TestCase):
    """Test the PasswordHistoryValidator class."""

    def setUp(self):
        """Set up test data."""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123'
        )
        # Ensure the user has pwdtk_data
        self.pwd_data = PwdData.get_or_create_for_user(self.user)
        self.validator = PasswordHistoryValidator(history_length=3)

    def test_validate_new_password(self):
        """Test validation with a new password."""
        self.validator.validate('newpassword123', self.user)

    def test_validate_old_password(self):
        """Test validation with the current password."""
        self.validator.password_changed('oldpassword123', self.user)

        with self.assertRaises(ValidationError):
            self.validator.validate('oldpassword123', self.user)

    def test_password_history_length(self):
        """Test that password history is limited to the specified length."""
        self.validator.password_changed('oldpassword123', self.user)

        # Change 1
        self.user.set_password('password2')
        self.user.save()
        self.validator.password_changed('password2', self.user)

        # Change 2
        self.user.set_password('password3')
        self.user.save()
        self.validator.password_changed('password3', self.user)

        # Change 3
        self.user.set_password('password4')
        self.user.save()
        self.validator.password_changed('password4', self.user)

        self.assertEqual(len(self.user.pwdtk_data.password_history), 3)

        # should be able to reuse old psw
        self.validator.validate('oldpassword123', self.user)

        with self.assertRaises(ValidationError):
            self.validator.validate('password2', self.user)

    def test_validate_without_user(self):
        """A password is validated before any user exists, e.g. on registration."""
        self.validator.validate('newpassword123')

    def test_validate_for_a_user_without_pwdtk_data(self):
        """A user who never logged in since pwdtk was installed has no history yet."""
        newcomer = self.User.objects.create_user(username='newcomer', password='oldpassword123')

        self.validator.validate('oldpassword123', newcomer)

    def test_password_changed_creates_pwdtk_data(self):
        """The history of a user without pwdtk data starts with the changed password."""
        newcomer = self.User.objects.create_user(username='newcomer', password='oldpassword123')

        pwd_data = self.validator.password_changed('oldpassword123', newcomer)

        self.assertEqual(pwd_data, PwdData.objects.get(user=newcomer))
        self.assertEqual([old_hash for _, old_hash in pwd_data.password_history], [newcomer.password])

    def test_custom_error_message(self):
        """The error message can be overridden through the validator options."""
        validator = PasswordHistoryValidator(history_length=3, error_messages={'password_reuse': 'nope'})
        validator.password_changed('oldpassword123', self.user)

        with self.assertRaises(ValidationError) as raised:
            validator.validate('oldpassword123', self.user)
        self.assertEqual(raised.exception.messages, ['nope'])

    def test_password_changed_without_user(self):
        """Django declares the user optional, then there is no history to update."""
        self.assertIsNone(self.validator.password_changed('newpassword123'))

    def test_get_help_text(self):
        """The help text tells how many passwords are remembered."""
        self.assertIn('3', self.validator.get_help_text())

# ------------------- Regex Password Validator --------


class RegexPasswordValidatorTest(TestCase):
    """Test the RegexPasswordValidator class."""

    def test_validate_no_pattern(self):
        """Test validation with no pattern set."""
        validator = RegexPasswordValidator(pattern="", pattern_info="")
        validator.validate("password123")
        validator.validate("any_password")
        validator.validate("@#$%^&*")

    def test_validate_with_pattern(self):
        """Test validation with a specific pattern."""
        pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
        pattern_info = "Password must be at least 8 characters and include both letters and numbers."
        validator = RegexPasswordValidator(pattern=pattern, pattern_info=pattern_info)

        # Valid passwords
        validator.validate("password123")
        validator.validate("12345abc")
        validator.validate("abcd1234")

        # Invalid passwords
        with self.assertRaises(ValidationError):
            validator.validate("pass123")
        with self.assertRaises(ValidationError):
            validator.validate("12345678")
        with self.assertRaises(ValidationError):
            validator.validate("password")

    @override_settings(
        PWDTK_PASSWORD_ALLOWED_PATTERN=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$',
        PWDTK_PASSWORD_DEFAULT_PATTERN_INFO="Must have letters and numbers, at least 8 chars long."
    )
    def test_settings_integration(self):
        """Test the validator uses settings correctly."""
        validator = RegexPasswordValidator()

        self.assertEqual(validator.pattern, r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')
        self.assertEqual(validator.pattern_info, "Must have letters and numbers, at least 8 chars long.")

        validator.validate("password123")

        with self.assertRaises(ValidationError):
            validator.validate("password")

    def test_custom_error_message(self):
        """The error message can be overridden through the validator options."""
        validator = RegexPasswordValidator(
            pattern=r'^\d+$', pattern_info="digits only",
            error_messages={'password_regex': 'bad: %(pattern_info)s'})

        with self.assertRaises(ValidationError) as raised:
            validator.validate("letters")
        self.assertEqual(raised.exception.messages, ['bad: digits only'])

    def test_get_help_text(self):
        """The help text is the pattern info, or a generic sentence without one."""
        validator = RegexPasswordValidator(pattern=r'^\d+$', pattern_info="digits only")
        self.assertEqual(validator.get_help_text(), "digits only")

        validator = RegexPasswordValidator(pattern=r'^\d+$', pattern_info="")
        self.assertIn("pattern", validator.get_help_text())

# ------------------- Password Age Validator --------


class PasswordAgeValidatorTest(TestCase):
    """Test the PasswordAgeValidator class."""

    def setUp(self):
        """Set up test data."""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123'
        )
        self.pwd_data = PwdData.get_or_create_for_user(self.user)
        self.validator = PasswordAgeValidator(max_age=30)

    def test_validate_rejects_the_current_password(self):
        """A renewal must not reuse the current password."""
        self.validator.validate('newpassword123', self.user)

        with self.assertRaises(ValidationError):
            self.validator.validate('oldpassword123', self.user)

    def test_password_changed_resets_must_renew(self):
        """A password change lifts a forced renewal and dates the password."""
        self.pwd_data.must_renew = True
        self.pwd_data.last_change_time = timezone.now() - datetime.timedelta(days=365)
        self.pwd_data.save()
        self.user.set_password('newpassword123')
        self.user.save()

        pwd_data = self.validator.password_changed('newpassword123', self.user)

        self.assertFalse(pwd_data.must_renew)
        pwd_data.refresh_from_db()
        self.assertFalse(pwd_data.must_renew)
        self.assertLess(timezone.now() - pwd_data.last_change_time, datetime.timedelta(minutes=1))

    def test_custom_error_message(self):
        """The error message can be overridden through the validator options."""
        validator = PasswordAgeValidator(max_age=30, error_messages={'password_not_changed': 'nope'})

        with self.assertRaises(ValidationError) as raised:
            validator.validate('oldpassword123', self.user)
        self.assertEqual(raised.exception.messages, ['nope'])

    def test_password_changed_without_user(self):
        """Django declares the user optional, then there is no age to update."""
        self.assertIsNone(self.validator.password_changed('newpassword123'))

    def test_get_help_text(self):
        """The help text tells that the password must actually change."""
        self.assertIn("current password", self.validator.get_help_text())
