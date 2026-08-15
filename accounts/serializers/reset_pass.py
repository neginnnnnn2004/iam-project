from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError


class PasswordResetWithBackupCodeSerializer(serializers.Serializer):
    """
     Serializer for resetting a user's password using a backup code.

     Validates the provided ``username`` and ``backup_code`` (typically used to
     authenticate the user when the primary password is lost), then validates
     and confirms a new password. Password strength is checked via Django's
     built-in validators, and all validation errors are returned in a
     dual-language (``fa`` / ``en``) format.

     Attributes:
         username (serializers.CharField): The user's username.
         backup_code (serializers.CharField): The one-time backup code used to
             authorize the password reset.
         new_password (serializers.CharField): Write-only new password, at
             least 8 characters, validated by Django's password validators.
         confirm_password (serializers.CharField): Write-only confirmation of
             the new password; must match ``new_password``.

     Example:
         >>> serializer = PasswordResetWithBackupCodeSerializer(data={
         ...     'username': 'dara_z',
         ...     'backup_code': 'ABC123XYZ',
         ...     'new_password': 'StrongPass123',
         ...     'confirm_password': 'StrongPass123'
         ... })
         >>> serializer.is_valid()
         True
     """
    username = serializers.CharField(required=True)
    backup_code = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        help_text="At least 8 characters."
    )

    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        help_text="Must match the password."
    )
    def validate_new_password(self, value: str) -> str:
        """
               Validate the new password using Django's built-in password validators.

               Runs ``validate_password`` on the submitted value. If validation fails,
               raises a ``ValidationError`` with dual-language (Persian/English)
               messages.

               Args:
                   value (str): The submitted new password.

               Returns:
                   str: The validated password value.

               Raises:
                   serializers.ValidationError: If the password does not meet Django's
                       password strength requirements.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                "fa": "رمز عبور وارد شده معتبر نیست (باید حداقل ۸ کاراکتر باشد و شامل حروف و اعداد باشد).",
                "en": "The password is not valid. It must be at least 8 characters long and contain both letters and numbers."
            })
        return value

    def validate(self, attrs: dict) -> dict:
        """
               Cross-field validation ensuring new_password and confirm_password match.

               Args:
                   attrs (dict): The dictionary of validated field values.

               Returns:
                   dict: The validated attributes.

               Raises:
                   serializers.ValidationError: If ``new_password`` does not equal
                       ``confirm_password``.
        """
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": {
                    "fa": "رمز عبور و تکرار آن مطابقت ندارند.",
                    "en": "Password and confirmation do not match."
                }
            })
        return attrs