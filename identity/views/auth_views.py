import json
import logging
from typing import Optional

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from identity.models import User
from identity.serializers.auth_serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    ProfileUpdateSerializer,
    ProfileUpdateResponseSerializer
)
from identity.utils import create_user_backup_codes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

logger = logging.getLogger('myapp.critical')


# ================== Helper Functions =====================
def get_client_meta(request):
    """
    Extracting network metadata for security logs
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'UNKNOWN')

    user_agent = request.META.get('HTTP_USER_AGENT', 'UNKNOWN')
    return {
        'ip': ip,
        'user_agent': user_agent
    }


def log_critical_event(action: str, status_type: str, request, user_id=None, error_code=None, extra=None):
    """
    Structured logging at critical and security-sensitive points in the system
    """
    client_info = get_client_meta(request)

    log_data = {
        'event_type': 'SECURITY_AUDIT',
        'action': action,
        'status': status_type,
        'timestamp': timezone.now().isoformat(),
        'client_ip': client_info['ip'],
        'user_agent': client_info['user_agent'],
    }

    if user_id is not None:
        log_data['user_id'] = user_id
    if error_code:
        log_data['error_code'] = error_code

    if extra:
        sensitive_keys = {
            'password',
            'confirm_password',
            'old_password',
            'new_password',
            'token',
            'access_token',
            'refresh_token',
            'authorization',
            'backup_codes',
        }
        safe_extra = {k: v for k, v in extra.items() if k not in sensitive_keys}
        log_data['extra'] = safe_extra

    log_message = json.dumps(log_data, ensure_ascii=False)

    if status_type in ['failed', 'error']:
        logger.error(log_message)
    elif status_type == 'success':
        logger.info(log_message)
    else:
        logger.debug(log_message)


# ================== 1. Registration =====================
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
        error_code = 10
        error_message = {
            "fa": "ثبت نام با خطا مواجه شد. لطفاً ورودی‌ها را بررسی کنید.",
            "en": "Registration failed. Please check your inputs."
        }

        is_missing_required = any(
            'required' in str(err) or 'blank' in str(err) or 'null' in str(err)
            for err in errors.values()
        )

        if is_missing_required:
            error_code = 12
            error_message = {
                "fa": "یک یا چند فیلد اجباری ارسال نشده است",
                "en": "One or more required fields are missing"
            }

        elif 'confirm_password' in errors or (
            'non_field_errors' in errors and any('match' in str(e).lower() or 'مطابقت' in str(e) for e in errors['non_field_errors'])
        ):
            error_code = 17
            error_message = {
                "fa": "رمز عبور با تکرار آن مطابقت ندارد",
                "en": "Password and confirm password do not match"
            }

        elif 'password' in errors:
            error_code = 13
            error_message = {
                "fa": "رمز عبور وارد شده معتبر نیست",
                "en": "Provided password is invalid"
            }

        elif 'phone' in errors:
            err_str = str(errors['phone']).lower()
            if 'unique' in err_str or 'exist' in err_str:
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

        elif 'email' in errors:
            err_str = str(errors['email']).lower()
            if 'unique' in err_str:
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

        elif 'username' in errors:
            username = str(request.data.get('username', '')).strip().lower()

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


# ================== 2. Login =====================
class UserLoginView(APIView):
    @swagger_auto_schema(
        operation_description="""
        User login and JWT token retrieval.

        Custom error codes for this endpoint:
        - code 10: Provided data (username or password format) is missing or invalid.
        - code 20: Username or password does not match database records (or user has been deleted).
        - code 21: User account status is inactive (Unverified, Pending, Suspended).
        """,
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: "Unauthorized (Code 20 / Code 21)",
            400: "Bad Request (Code 10)",
        }
    )
    def post(self, request):
        username = request.data.get('username', 'unknown')

        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            log_critical_event(
                action='login',
                status_type='failed',
                request=request,
                error_code=10,
                extra={
                    'attempted_username': username,
                    'validation_errors': serializer.errors,
                }
            )
            return Response({
                "error_code": 10,
                "message": {
                    "fa": "اطلاعات ارسالی برای ورود ناقص یا نامعتبر است.",
                    "en": "Provided login data is incomplete or invalid."
                },
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user: Optional[User] = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )

        if user is None or user.status == 'deleted':
            # Login failure due to invalid username/password or deleted user (to prevent brute-force attacks)
            log_critical_event(
                action='login',
                status_type='failed',
                request=request,
                error_code=20,
                extra={
                    'attempted_username': username,
                    'reason': 'Invalid credentials or deleted account'
                }
            )

            return Response({
                "error_code": 20,
                "message": {
                    "fa": "نام کاربری یا رمز عبور اشتباه است.",
                    "en": "Invalid username or password."
                },
                "detail": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        if user.status in ['unverified', 'pending', 'suspended']:
            status_messages = {
                'unverified': {
                    "fa": "حساب کاربری شما توسط ادمین تایید نشده است",
                    "en": "Your account has not been verified by the admin"
                },
                'pending': {
                    "fa": "حساب کاربری شما در انتظار بررسی است",
                    "en": "Your account is pending approval"
                },
                'suspended': {
                    "fa": "حساب کاربری شما مسدود شده است",
                    "en": "Your account has been suspended"
                }
            }

            # Login failure due to invalid username/password or deleted user (to prevent brute-force attacks)
            log_critical_event(
                action='login',
                status_type='failed',
                request=request,
                user_id=user.id,
                error_code=21,
                extra={
                    'username': user.username,
                    'account_status': user.status
                }
            )

            return Response({
                "error_code": 21,
                "message": status_messages.get(user.status, {
                    "fa": "وضعیت حساب نامعتبر",
                    "en": "Invalid account status"
                }),
                "detail": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        if user.status == 'active':
            refresh = RefreshToken.for_user(user)

            # Successful login log
            log_critical_event(
                action='login',
                status_type='success',
                request=request,
                user_id=user.id,
                extra={'username': user.username}
            )

            return Response({
                'access_token': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)

        return Response({
            "error_code": 21,
            "message": {
                "fa": "وضعیت حساب کاربری شما نامعتبر است.",
                "en": "Your account status is invalid."
            },
            "detail": None
        }, status=status.HTTP_401_UNAUTHORIZED)


# ================== 3. Profile Update =====================
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, partial=False):
        user = request.user

        serializer = ProfileUpdateSerializer(
            instance=user,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()

            # Check which sensitive fields were actually modified and verified
            important_fields = ['phone', 'password']
            changed_important = [f for f in serializer.validated_data.keys() if f in important_fields]

            if changed_important:
                # Log successful changes to sensitive profile information
                log_critical_event(
                    action='profile_update',
                    status_type='success',
                    request=request,
                    user_id=user.id,
                    extra={
                        'username': user.username,
                        'changed_sensitive_fields': changed_important,
                    }
                )

            return Response({
                'message': {
                    "fa": "پروفایل با موفقیت بروزرسانی شد",
                    "en": "Profile updated successfully"
                },
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        errors = serializer.errors
        if 'password' in errors:
            error_code = 30
            error_message = {
                "fa": "رمز عبور وارد شده معتبر نیست",
                "en": "Invalid password provided"
            }

        elif 'confirm_password' in errors:
            error_code = 30
            error_message = {
                "fa": "تکرار رمز عبور معتبر نیست",
                "en": "Password confirmation does not match"
            }

        elif 'non_field_errors' in errors:
            non_field_str = str(errors['non_field_errors'])
            if any(keyword in non_field_str for keyword in ['رمز عبور', 'password', 'تطابق']):
                error_code = 30
                error_message = {
                    "fa": "رمز عبور وارد شده معتبر نیست",
                    "en": "Invalid password provided"
                }
            else:
                error_code = 10
                error_message = {
                    "fa": "اطلاعات ارسالی نامعتبر است",
                    "en": "Provided data is invalid"
                }

        elif 'phone' in errors and 'قبلاً ثبت' in str(errors['phone']):
            error_code = 31
            error_message = {
                "fa": "شماره تلفن وارد شده تکراری است",
                "en": "Provided phone number is already in use"
            }

        elif 'phone' in errors:
            error_code = 31
            error_message = {
                "fa": "فرمت شماره تلفن نامعتبر است",
                "en": "Invalid phone number format"
            }

        else:
            error_code = 10
            error_message = {
                "fa": "ویرایش اطلاعات پروفایل انجام نشد.",
                "en": "Profile update failed."
            }

        # Log errors related to changing sensitive information such as passwords and phone numbers
        log_critical_event(
            action='profile_update',
            status_type='failed',
            request=request,
            user_id=user.id,
            error_code=error_code,
            extra={
                'username': user.username,
                'validation_errors': errors
            }
        )

        return Response({
            "error_code": error_code,
            "message": error_message,
            "detail": errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""
        Partial update of user profile information.

        Custom error codes for this endpoint:
        - code 10: Invalid input data.
        - code 30: Provided password is invalid.
        - code 31: Provided phone number is invalid or already in use.
        """,
        request_body=ProfileUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=ProfileUpdateResponseSerializer
            ),
            400: "Bad Request (Code 10,30,31)",
            401: "Unauthorized",
        }
    )
    def patch(self, request):
        return self.update(request, partial=True)