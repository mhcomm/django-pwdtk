from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from pwdtk.validators import RegexPasswordValidator, PasswordHistoryValidator
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
