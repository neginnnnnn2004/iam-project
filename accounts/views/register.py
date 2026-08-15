from rest_framework import status

from rest_framework.response import Response
from rest_framework.views import APIView

from identity.models import User
from accounts.serializers.register import (UserRegisterSerializer,)

from accounts.utils import create_user_backup_codes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from identity.services import log_critical_event

# ================== Registration =====================
class UserRegisterView(APIView):
    """
    Handles new user registration, generates backup recovery codes,
    and returns localized responses with granular custom error codes.
    """

    @swagger_auto_schema(
        operation_description="""
        Register a new user and retrieve one-time backup codes.

        Custom error codes for this endpoint:
        - code 10: Invalid input data (e.g., username format).
        - code 11: Username already exists.
        - code 12: One or more required fields are missing or empty.
        - code 13: Provided password is invalid (weak or bad format).
        - code 14: Phone number is already registered.
        - code 15: Email address is already registered.
        - code 16: Invalid email or phone number format.
        - code 17: Password and confirm_password do not match.
        """,
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "fa": openapi.Schema(type=openapi.TYPE_STRING),
                                "en": openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        "user": openapi.Schema(type=openapi.TYPE_OBJECT),
                        "backup_codes": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING)
                        ),
                    }
                )
            ),
            400: "Bad Request (Code 10,11,12,13,14,15,16,17)",
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            raw_codes = create_user_backup_codes(user, count=8)

            # Successful registration log
            log_critical_event(
                action="register",
                status_type='success',
                request=request,
                user_id=user.id,
                extra={
                    'username': user.username,
                    'email': user.email,
                    'phone': str(user.phone) if user.phone else None,
                }
            )

            return Response({
                "message": {
                    "fa": "ثبت نام شما با موفقیت انجام شد. لطفاً کدهای پشتیبان خود را در جایی امن ذخیره کنید.",
                    "en": "Registration successful. Please store your backup codes in a safe place."
                },
                "user": serializer.data,
                "backup_codes": raw_codes
            }, status=status.HTTP_201_CREATED)

        errors = serializer.errors

        # 12 - Missing required fields
        is_missing_required = any(
            getattr(error, 'code', None) in ['required','blank','null']
            for field_errors in errors.values()
            for error in field_errors
        )

        if is_missing_required:
            error_code = 12
            error_message = {
                "fa": "یک یا چند فیلد اجباری ارسال نشده است",
                "en": "One or more required fields are missing"
            }

        # 17 - Password confirmation mismatch
        elif 'confirm_password' in errors or (
                'non_field_errors' in errors
                and any(
            'match' in str(error).lower()
            or 'مطابقت' in str(error)
            for error in errors['non_field_errors']
        )
        ):
            error_code = 17
            error_message = {
                "fa": "رمز عبور با تکرار آن مطابقت ندارد",
                "en": "Password and confirm password do not match"
            }

        # 13 - Invalid password
        elif 'password' in errors:
            error_code = 13
            error_message = {
                "fa": "رمز عبور وارد شده معتبر نیست",
                "en": "Provided password is invalid"
            }

        # 14 / 16 - Phone
        elif 'phone' in errors:
            err_str = str(errors['phone']).lower()

            if (
                    'registered' in err_str
                    or 'unique' in err_str
                    or 'exist' in err_str
            ):
                error_code = 14
                error_message = {
                    "fa": "شماره تلفن تکراری است",
                    "en": "Phone number is already registered"
                }
            else:
                error_code = 16
                error_message = {
                    "fa": "فرمت شماره تلفن نامعتبر است",
                    "en": "Invalid phone number format"
                }

        # 15 / 16 - Email
        elif 'email' in errors:
            err_str = str(errors['email']).lower()

            if (
                    'registered' in err_str
                    or 'unique' in err_str
                    or 'exist' in err_str
            ):
                error_code = 15
                error_message = {
                    "fa": "ایمیل تکراری است",
                    "en": "Email address is already registered"
                }
            else:
                error_code = 16
                error_message = {
                    "fa": "فرمت ایمیل نامعتبر است",
                    "en": "Invalid email address format"
                }

        # 11 / 10 - Username
        elif 'username' in errors:
            username = str(
                request.data.get('username', '')
            ).strip().lower()

            if User.objects.filter(username=username).exists():
                error_code = 11
                error_message = {
                    "fa": "نام کاربری تکراری است",
                    "en": "Username already exists"
                }
            else:
                error_code = 10
                error_message = {
                    "fa": "فرمت نام کاربری اشتباه است",
                    "en": "Invalid username format"
                }

        else:
            error_code = 10
            error_message = {
                "fa": "ثبت نام با خطا مواجه شد. لطفاً ورودی‌ها را بررسی کنید.",
                "en": "Registration failed. Please check your inputs."
            }
        # Registration failure log (including all validation errors)
        log_critical_event(
            action="register",
            status_type='failed',
            request=request,
            error_code=error_code,
            extra={
                'attempted_username': request.data.get('username'),
                'attempted_email': request.data.get('email'),
                'attempted_phone': request.data.get('phone'),
                'validation_errors': errors,
            }
        )

        return Response({
            "error_code": error_code,
            "message": error_message,
            'detail': errors
        }, status=status.HTTP_400_BAD_REQUEST)

