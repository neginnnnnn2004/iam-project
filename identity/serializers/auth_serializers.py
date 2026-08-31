# import re
# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError as DjangoValidationError
# from rest_framework import serializers
# from identity.models import User
#
# class SwaggerEmailField(serializers.EmailField):
#     class Meta:
#         swagger_schema_fields = {
#             "min_length": None,
#         }
#
# class UserRegisterSerializer(serializers.ModelSerializer):
#     """
#     Serializer for user registration.
#     """
#
#     username = serializers.CharField(
#         required=True,
#         min_length=5,
#         max_length=20,
#         help_text="5-20 characters; letters, numbers, underscores, and hyphens only."
#     )
#
#     password = serializers.CharField(
#         write_only=True,
#         required=True,
#         min_length=8,
#         help_text="At least 8 characters."
#     )
#
#     confirm_password = serializers.CharField(
#         write_only=True,
#         required=True,
#         min_length=8,
#         help_text="Must match the password."
#     )
#
#     email = SwaggerEmailField(
#         required=True,
#         help_text="Valid and unique email address."
#     )
#
#     phone = serializers.RegexField(
#         regex=r'^09\d{9}$',
#         required=True,
#         min_length=11,
#         max_length=11,
#         help_text="Iranian mobile number (09xxxxxxxxx)."
#     )
#
#     first_name = serializers.CharField(
#         required=False,
#         allow_blank=True,
#         help_text="Optional first name."
#     )
#
#     last_name = serializers.CharField(
#         required=False,
#         allow_blank=True,
#         help_text="Optional last name."
#     )
#
#     class Meta:
#         model = User
#         fields = (
#             'username',
#             'password',
#             'confirm_password',
#             'email',
#             'phone',
#             'first_name',
#             'last_name'
#         )
#     def validate_username(self, value: str) -> str:
#         """
#         Check if the username is unique and normalize it to lowercase.
#         """
#         username = value.strip().lower()
#
#         if len(username) < 5:
#             raise serializers.ValidationError({
#                 "fa": "نام کاربری باید حداقل ۵ کاراکتر باشد.",
#                 "en": "Username must be at least 5 characters long."
#             })
#
#         if username.isdigit():
#             raise serializers.ValidationError({
#                 "fa": "نام کاربری نمی‌تواند فقط شامل اعداد باشد.",
#                 "en": "Username cannot consist only of numbers."
#             })
#
#         if User.objects.filter(username=username).exists():
#             raise serializers.ValidationError({
#                 "fa": "این نام کاربری قبلاً ثبت شده است.",
#                 "en": "This username is already registered."
#             })
#
#         return username
#
#     def validate_password(self, value: str) -> str:
#         """
#         Validate the password using Django's built-in password validators
#         and return dual-language error messages.
#         """
#         try:
#             validate_password(value)
#         except DjangoValidationError as e:
#             raw_errors_en = " ".join(e.messages)
#             raise serializers.ValidationError({
#                 "fa": "رمز عبور وارد شده معتبر نیست (باید حداقل ۸ کاراکتر باشد و شامل حروف و اعداد باشد).",
#                 "en": raw_errors_en
#             })
#         return value
#
#     def validate_email(self, value: str) -> str:
#         """
#         Normalize email to lowercase and ensure uniqueness.
#         """
#         if value:
#             email = value.lower()
#             if User.objects.filter(email=email).exists():
#                 raise serializers.ValidationError({
#                     "fa": "این آدرس ایمیل از قبل ثبت شده است.",
#                     "en": "This email address is already registered."
#                 })
#             return email
#         return value
#
#     def validate_phone(self, value: str) -> str:
#         """
#         Validate Iranian mobile phone number format (09xxxxxxxxx) and uniqueness.
#         """
#         if value:
#             value = value.strip()
#
#             if not re.match(r'^09\d{9}$', value):
#                 raise serializers.ValidationError({
#                     "fa": "شماره تلفن باید با 09 شروع شده و 11 رقم باشد.",
#                     "en": "Phone number must start with 09 and contain 11 digits."
#                 })
#
#             if User.objects.filter(phone=value).exists():
#                 raise serializers.ValidationError({
#                     "fa": "این شماره تلفن قبلاً ثبت شده است.",
#                     "en": "This phone number is already registered."
#                 })
#
#         return value
#
#     def validate(self, attrs: dict) -> dict:
#         """
#         Ensure password and confirm_password fields match.
#         """
#         if attrs.get('password') != attrs.get('confirm_password'):
#             raise serializers.ValidationError({
#                 "confirm_password": {
#                     "fa": "رمز عبور و تکرار آن مطابقت ندارند.",
#                     "en": "Password and confirmation do not match."
#                 }
#             })
#         return attrs
#
#     def create(self, validated_data: dict) -> User:
#         """
#         Create and return a new User instance after removing confirm_password.
#         """
#         validated_data.pop('confirm_password', None)
#         return User.objects.create_user(**validated_data)
#
#
# class UserLoginSerializer(serializers.Serializer):
#     """
#     Serializer for user login request payload.
#     """
#     username = serializers.CharField()
#     password = serializers.CharField()
#
#
# class ProfileUpdateSerializer(serializers.ModelSerializer):
#     """
#     Serializer for updating user profile fields including password and phone number.
#     """
#     first_name = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
#     last_name = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
#     password = serializers.CharField(
#         write_only=True,
#         required=False,
#         allow_blank=True,
#         min_length=8,
#         help_text="New password must be at least 8 characters long.",
#         style={'input_type': 'password'}
#     )
#
#     confirm_password = serializers.CharField(
#         write_only=True,
#         required=False,
#         allow_blank=True,
#         min_length=8,
#         help_text="Must match the new password.",
#         style={'input_type': 'password'}
#     )
#
#     phone = serializers.RegexField(
#         regex=r'^09\d{9}$',
#         required=False,
#         allow_blank=True,
#         min_length=11,
#         max_length=11,
#         help_text="Iranian mobile number. Must start with 09 and contain exactly 11 digits."
#     )
#     class Meta:
#         model = User
#         fields = ('first_name', 'last_name', 'password', 'confirm_password', 'phone')
#
#     def validate_password(self, value: str) -> str:
#         """
#         Validate new password strength if provided and return dual-language errors.
#         """
#         if value and value.strip():
#             try:
#                 validate_password(value)
#             except DjangoValidationError as e:
#                 raw_errors_en = " ".join(e.messages)
#                 raise serializers.ValidationError({
#                     "fa": "رمز عبور وارد شده معتبر نیست (باید حداقل ۸ کاراکتر باشد و شامل حروف و اعداد باشد).",
#                     "en": raw_errors_en
#                 })
#         return value
#
#     def validate_phone(self, value: str) -> str:
#         """
#         Validate phone number format and uniqueness excluding current user instance.
#         """
#         if value and value.strip():
#             value = value.strip()
#             if not re.match(r'^09\d{9}$', value):
#                 raise serializers.ValidationError({
#                     "fa": "شماره تلفن باید با 09 شروع شده و 11 رقم باشد.",
#                     "en": "Phone number must start with 09 and contain 11 digits."
#                 })
#
#             if self.instance:
#                 if User.objects.filter(phone=value).exclude(pk=self.instance.pk).exists():
#                     raise serializers.ValidationError({
#                         "fa": "این شماره تلفن قبلاً توسط کاربر دیگری ثبت شده است.",
#                         "en": "This phone number is already registered by another user."
#                     })
#             else:
#                 if User.objects.filter(phone=value).exists():
#                     raise serializers.ValidationError({
#                         "fa": "این شماره تلفن قبلاً ثبت شده است.",
#                         "en": "This phone number is already registered."
#                     })
#         return value
#
#     def validate(self, attrs: dict) -> dict:
#         """
#         Ensure both password and confirm_password are provided together and match.
#         """
#         password = attrs.get('password')
#         confirm_password = attrs.get('confirm_password')
#
#         if password is not None and password != '':
#             if confirm_password is None or confirm_password == '':
#                 raise serializers.ValidationError({
#                     "confirm_password": {
#                         "fa": "برای تغییر رمز عبور، تکرار رمز عبور الزامی است.",
#                         "en": "Confirm password is required when changing password."
#                     }
#                 })
#             if password != confirm_password:
#                 raise serializers.ValidationError({
#                     "confirm_password": {
#                         "fa": "رمز عبور و تکرار آن مطابقت ندارند.",
#                         "en": "Password and confirmation do not match."
#                     }
#                 })
#
#         if confirm_password is not None and confirm_password != '':
#             if password is None or password == '':
#                 raise serializers.ValidationError({
#                     "password": {
#                         "fa": "برای تغییر رمز عبور، رمز عبور جدید الزامی است.",
#                         "en": "New password is required when confirm password is provided."
#                     }
#                 })
#
#         return attrs
#
#     def update(self, instance: User, validated_data: dict) -> User:
#         """
#         Update profile fields and set password if a new one was provided.
#         """
#         password = validated_data.pop('password', None)
#         validated_data.pop('confirm_password', None)
#
#         if password:
#             instance.set_password(password)
#         return super().update(instance, validated_data)
#
#
# class ProfileUpdateResponseSerializer(serializers.Serializer):
#     """
#     Serializer representing the successful response structure after profile update.
#     """
#     message = serializers.DictField(child=serializers.CharField())
#     data = ProfileUpdateSerializer()