from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError


class PasswordResetWithBackupCodeSerializer(serializers.Serializer):
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
        Validate the password using Django's built-in password validators
        and return dual-language error messages.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raw_errors_en = " ".join(e.messages)
            raise serializers.ValidationError({
                "fa": "رمز عبور وارد شده معتبر نیست (باید حداقل ۸ کاراکتر باشد و شامل حروف و اعداد باشد).",
                "en": raw_errors_en
            })
        return value

    def validate(self, attrs: dict) -> dict:
        """
        Ensure password and confirm_password fields match.
        """
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": {
                    "fa": "رمز عبور و تکرار آن مطابقت ندارند.",
                    "en": "Password and confirmation do not match."
                }
            })
        return attrs