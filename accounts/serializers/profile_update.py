import re
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from identity.models import User


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a user's profile fields.

    Supports partial updates of ``first_name``, ``last_name``, ``phone`` and
    optionally changing the password. When a password change is requested,
    both ``password`` and ``confirm_password`` must be provided together and
    must match. All validation errors are returned in a dual-language format
    (``fa`` / ``en``) to support both Persian and English clients.

    Attributes:
        first_name (serializers.CharField): Optional user first name.
        last_name (serializers.CharField): Optional user last name.
        password (serializers.CharField): Optional new password (write-only).
            Must be at least 8 characters and pass Django's password validators.
        confirm_password (serializers.CharField): Optional confirmation of the
            new password (write-only). Must match ``password``.
        phone (serializers.RegexField): Optional Iranian mobile number matching
            the pattern ``^09\\d{9}$``. Must be unique across users.

    Example:
        >>> serializer = ProfileUpdateSerializer(
        ...     instance=user,
        ...     data={'first_name': 'Dara', 'phone': '09123456789'},
        ...     partial=True
        ... )
        >>> serializer.is_valid()
        True
        >>> serializer.save()
    """
    first_name = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    last_name = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        min_length=8,
        help_text="New password must be at least 8 characters long.",
        style={'input_type': 'password'}
    )

    confirm_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        min_length=8,
        help_text="Must match the new password.",
        style={'input_type': 'password'}
    )

    phone = serializers.RegexField(
        regex=r'^09\d{9}$',
        required=False,
        allow_blank=True,
        min_length=11,
        max_length=11,
        help_text="Iranian mobile number. Must start with 09 and contain exactly 11 digits."
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'password', 'confirm_password', 'phone')

    def validate_password(self, value: str) -> str:
        """
        Validate new password strength if provided and return dual-language errors.
        """
        if value and value.strip():
            try:
                validate_password(value)
            except DjangoValidationError as e:
                raw_errors_en = " ".join(e.messages)
                raise serializers.ValidationError({
                    "fa": "رمز عبور وارد شده معتبر نیست (باید حداقل ۸ کاراکتر باشد و شامل حروف و اعداد باشد).",
                    "en": raw_errors_en
                })
        return value

    def validate_phone(self, value: str) -> str:
        """
        Validate phone number format and uniqueness excluding current user instance.
        """
        if value and value.strip():
            value = value.strip()
            if not re.match(r'^09\d{9}$', value):
                raise serializers.ValidationError({
                    "fa": "شماره تلفن باید با 09 شروع شده و 11 رقم باشد.",
                    "en": "Phone number must start with 09 and contain 11 digits."
                })

            if self.instance:
                if User.objects.filter(phone=value).exclude(pk=self.instance.pk).exists():
                    raise serializers.ValidationError({
                        "fa": "این شماره تلفن قبلاً توسط کاربر دیگری ثبت شده است.",
                        "en": "This phone number is already registered by another user."
                    })
            else:
                if User.objects.filter(phone=value).exists():
                    raise serializers.ValidationError({
                        "fa": "این شماره تلفن قبلاً ثبت شده است.",
                        "en": "This phone number is already registered."
                    })
        return value

    def validate(self, attrs: dict) -> dict:
        """
        Ensure both password and confirm_password are provided together and match.
        """
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password is not None and password != '':
            if confirm_password is None or confirm_password == '':
                raise serializers.ValidationError({
                    "confirm_password": {
                        "fa": "برای تغییر رمز عبور، تکرار رمز عبور الزامی است.",
                        "en": "Confirm password is required when changing password."
                    }
                })
            if password != confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": {
                        "fa": "رمز عبور و تکرار آن مطابقت ندارند.",
                        "en": "Password and confirmation do not match."
                    }
                })

        if confirm_password is not None and confirm_password != '':
            if password is None or password == '':
                raise serializers.ValidationError({
                    "password": {
                        "fa": "برای تغییر رمز عبور، رمز عبور جدید الزامی است.",
                        "en": "New password is required when confirm password is provided."
                    }
                })

        return attrs

    def update(self, instance: User, validated_data: dict) -> User:
        """
          Validate the phone number format and uniqueness.

          Ensures the phone matches the Iranian mobile pattern and is not already
          used by another user. When updating an existing instance, the current
          user is excluded from the uniqueness check.

          Args:
              value (str): The submitted phone number.

          Returns:
              str: The validated, stripped phone number.

          Raises:
              serializers.ValidationError: If the format is invalid or the number
                  is already registered by another user.
          """
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)

        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class ProfileUpdateResponseSerializer(serializers.Serializer):
    """
    Serializer representing the successful response structure after profile update.
    """
    message = serializers.DictField(child=serializers.CharField())
    data = ProfileUpdateSerializer()