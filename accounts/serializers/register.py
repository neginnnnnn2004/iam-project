import re
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from identity.models import User


class SwaggerEmailField(serializers.EmailField):
    """
    Custom EmailField that removes the default minimum length constraint
    from the generated Swagger/OpenAPI schema.

    By default, DRF's ``EmailField`` may impose a ``min_length`` in the
    generated schema. This subclass overrides that behavior by setting
    ``min_length`` to ``None`` in the swagger schema fields, ensuring the
    documented API does not incorrectly require a minimum email length.

    Attributes:
        Meta.swagger_schema_fields (dict): Overrides for the generated
            OpenAPI schema, specifically disabling ``min_length``.
    """
    class Meta:
        swagger_schema_fields = {
            "min_length": None,
        }


class UserRegisterSerializer(serializers.ModelSerializer):
    """
      Serializer for user registration.

      Validates and creates a new ``User`` instance. Enforces uniqueness and
      format rules for ``username``, ``email`` and ``phone``, validates password
      strength via Django's built-in validators, and ensures ``password`` matches
      ``confirm_password``. All validation errors are returned in a dual-language
      (``fa`` / ``en``) format.

      Attributes:
          username (serializers.CharField): Unique username, 5-20 characters,
              normalized to lowercase.
          password (serializers.CharField): Write-only password, at least 8
              characters, validated by Django's password validators.
          confirm_password (serializers.CharField): Write-only confirmation of
              the password; must match ``password``.
          email (SwaggerEmailField): Unique, valid email address, normalized to
              lowercase.
          phone (serializers.RegexField): Unique Iranian mobile number matching
              ``^09\\d{9}$``.
          first_name (serializers.CharField): Optional first name.
          last_name (serializers.CharField): Optional last name.

      Example:
          >>> serializer = UserRegisterSerializer(data={
          ...     'username': 'dara_z',
          ...     'password': 'StrongPass123',
          ...     'confirm_password': 'StrongPass123',
          ...     'email': 'dara@test.com',
          ...     'phone': '09123456789'
          ... })
          >>> serializer.is_valid()
          True
          >>> user = serializer.save()
      """

    username = serializers.CharField(
        required=True,
        min_length=5,
        max_length=20,
        help_text="5-20 characters; letters, numbers, underscores, and hyphens only."
    )

    password = serializers.CharField(
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

    email = SwaggerEmailField(
        required=True,
        help_text="Valid and unique email address."
    )

    phone = serializers.RegexField(
        regex=r'^09\d{9}$',
        required=True,
        min_length=11,
        max_length=11,
        help_text="Iranian mobile number (09xxxxxxxxx)."
    )

    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional first name."
    )

    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional last name."
    )

    class Meta:
        model = User
        fields = (
            'username',
            'password',
            'confirm_password',
            'email',
            'phone',
            'first_name',
            'last_name'
        )

    def validate_username(self, value: str) -> str:

        """
        Validate the username for uniqueness and normalize it to lowercase.

        Strips whitespace, converts to lowercase, and checks that the result
        is at least 5 characters, is not purely numeric, and is not already
        registered.

        Args:
            value (str): The submitted username.

        Returns:
            str: The normalized (lowercased, stripped) username.

        Raises:
            serializers.ValidationError: If the username is too short, consists
                only of digits, or is already registered.
        """
        username = value.strip().lower()

        if len(username) < 5:
            raise serializers.ValidationError({
                "fa": "نام کاربری باید حداقل ۵ کاراکتر باشد.",
                "en": "Username must be at least 5 characters long."
            })

        if username.isdigit():
            raise serializers.ValidationError({
                "fa": "نام کاربری نمی‌تواند فقط شامل اعداد باشد.",
                "en": "Username cannot consist only of numbers."
            })

        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise serializers.ValidationError({
                "fa": "نام کاربری فقط می‌تواند شامل حروف، اعداد، _ و - باشد.",
                "en": "Username can only contain letters, numbers, underscores, and hyphens."
            })

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({
                "fa": "این نام کاربری قبلاً ثبت شده است.",
                "en": "This username is already registered."
            })

        return username

    def validate_password(self, value: str) -> str:
        """
          Validate the password using Django's built-in password validators.

          Runs ``validate_password`` on the submitted value. If the password fails
          any of Django's default strength checks, raises a ``ValidationError`` with
          a fixed, dual-language (Persian/English) message so the client receives a
          consistent, predictable error regardless of which validator failed.

          Args:
              value (str): The submitted password to validate.

          Returns:
              str: The validated password value unchanged.

          Raises:
              serializers.ValidationError: If the password does not meet Django's
                  password strength requirements. The error contains both a Persian
                  (``fa``) and English (``en``) message.
          """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                "fa": "رمز عبور وارد شده معتبر نیست (باید حداقل ۸ کاراکتر باشد و شامل حروف و اعداد باشد).",
                "en": "The password is not valid. It must be at least 8 characters long and contain both letters and numbers."
            })
        return value

    def validate_email(self, value: str) -> str:
        """
        Normalize the email to lowercase and ensure it is unique.

        Args:
            value (str): The submitted email address.

        Returns:
            str: The normalized (lowercased) email address, or the original
                value if it is empty.

        Raises:
            serializers.ValidationError: If the email is already registered.
        """
        if value:
            email = value.lower()
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({
                    "fa": "این آدرس ایمیل از قبل ثبت شده است.",
                    "en": "This email address is already registered."
                })
            return email
        return value

    def validate_phone(self, value: str) -> str:

        """
        Validate the Iranian mobile phone number format and uniqueness.

        Strips whitespace, checks the value against the pattern ``^09\\d{9}$``,
        and verifies it is not already registered.

        Args:
            value (str): The submitted phone number.

        Returns:
            str: The validated, stripped phone number.

        Raises:
            serializers.ValidationError: If the format is invalid or the number
                is already registered.
        """
        if value:
            value = value.strip()

            if not re.match(r'^09\d{9}$', value):
                raise serializers.ValidationError({
                    "fa": "شماره تلفن باید با 09 شروع شده و 11 رقم باشد.",
                    "en": "Phone number must start with 09 and contain 11 digits."
                })

            if User.objects.filter(phone=value).exists():
                raise serializers.ValidationError({
                    "fa": "این شماره تلفن قبلاً ثبت شده است.",
                    "en": "This phone number is already registered."
                })

        return value

    def validate(self, attrs: dict) -> dict:
        """
              Cross-field validation ensuring password and confirm_password match.

              Args:
                  attrs (dict): The dictionary of validated field values.

              Returns:
                  dict: The validated attributes.

              Raises:
                  serializers.ValidationError: If ``password`` does not equal
                      ``confirm_password``.
              """
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": {
                    "fa": "رمز عبور و تکرار آن مطابقت ندارند.",
                    "en": "Password and confirmation do not match."
                }
            })
        return attrs

    def create(self, validated_data: dict) -> User:
        """
        Create and return a new User instance.

        Removes ``confirm_password`` from the validated data (since it is not
        a model field) and delegates user creation to ``User.objects.create_user``,
        which handles password hashing.

        Args:
            validated_data (dict): The validated field values.

        Returns:
            User: The newly created user instance.
        """
        validated_data.pop('confirm_password', None)
        return User.objects.create_user(**validated_data)
