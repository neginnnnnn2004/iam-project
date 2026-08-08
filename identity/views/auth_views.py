from django.contrib.auth import authenticate
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from identity.serializers.auth_serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    ProfileUpdateSerializer,
    ProfileUpdateResponseSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from identity.utils import create_user_backup_codes
from typing import Optional
from identity.models import User
import logging
import time

logger = logging.getLogger('myapp.critical')


# ================== Helper Functions =====================
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def log_critical_event(action, status, user_id=None, error_code=None, extra=None):
    """
    لاگ نقاط حیاتی
    """
    log_data = {
        'action': action,
        'status': status,
        'timestamp': time.time(),
    }

    if user_id:
        log_data['user_id'] = user_id
    if error_code:
        log_data['error_code'] = error_code
    if extra:
        safe_extra = {k: v for k, v in extra.items() if k not in ['password', 'token']}
        log_data['extra'] = safe_extra

    log_message = json.dumps(log_data, ensure_ascii=False)

    if status in ['failed', 'error']:
        logger.error(log_message)
    elif status == 'success' and action in ['register', 'login']:
        logger.info(log_message)
    else:
        logger.debug(log_message)


# ================== 1. Registration =====================
class UserRegisterView(APIView):
    @swagger_auto_schema(
        operation_description="""
        Register a new user and retrieve one-time backup codes.

        Custom error codes for this endpoint:
        - code 10: Invalid input data (username or password format).
        - code 11: Username already exists.
        - code 12: One or more required fields are missing or empty.
        - code 13: Provided password is invalid.
        - code 14: Phone number is already registered.
        - code 15: Email address is already registered.
        - code 16: Invalid email or phone number format.
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
            400: "Bad Request (Code 10,11,12,13,14,15,16)",
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            raw_codes = create_user_backup_codes(user, count=8)

            log_critical_event(
                action="register",
                status='success',
                user_id=user.id,
                extra={
                    'username': user.username,
                    'email': user.email,
                    'phone': user.phone,
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

        elif 'password' in errors or 'non_field_errors' in errors or 'confirm_password' in errors:
            error_code = 13
            error_message = {
                "fa": "رمز عبور وارد شده معتبر نیست یا با تکرار آن مطابقت ندارد",
                "en": "Invalid password or password confirmation does not match"
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
            err_str = str(errors['username']).lower()
            if 'unique' in err_str or 'exist' in err_str:
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

        if error_code in [11, 13, 14, 15]:
            log_critical_event(
                action="register",
                status='failed',
                error_code=error_code,
                extra={
                    'username': request.data.get('username'),
                    'email': request.data.get('email'),
                    'phone': request.data.get('phone'),
                    'error': serializer.errors,
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
                status='failed',
                error_code=10,
                extra={
                    'username': username,
                    'error': serializer.errors,
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
            log_critical_event(
                action='login',
                status='failed',
                error_code=20,
                extra={
                    'username': username,
                    'ip': get_client_ip(request)
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

            log_critical_event(
                action='login',
                status='failed',
                user_id=user.id,
                error_code=21,
                extra={
                    'username': user.username,
                    'status': user.status
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

            log_critical_event(
                action='login',
                status='success',
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

            important_fields = ['email', 'phone', 'password']
            changed_important = [f for f in request.data.keys() if f in important_fields]

            if changed_important:
                log_critical_event(
                    action='profile_update',
                    status='success',
                    user_id=user.id,
                    extra={
                        'username': user.username,
                        'changed_fields': changed_important,
                        'ip': get_client_ip(request)
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

        elif 'email' in errors and 'already' in str(errors['email']).lower():
            error_code = 31
            error_message = {
                "fa": "ایمیل وارد شده تکراری است",
                "en": "Provided email is already in use"
            }

        elif 'phone' in errors and 'قبلاً ثبت' in str(errors['phone']):
            error_code = 32
            error_message = {
                "fa": "شماره تلفن وارد شده تکراری است",
                "en": "Provided phone number is already in use"
            }

        elif 'phone' in errors:
            error_code = 32
            error_message = {
                "fa": "فرمت شماره تلفن نامعتبر است",
                "en": "Invalid phone number format"
            }

        elif 'email' in errors:
            error_code = 31
            error_message = {
                "fa": "فرمت ایمیل نامعتبر است",
                "en": "Invalid email address format"
            }

        else:
            error_code = 10
            error_message = {
                "fa": "ویرایش اطلاعات پروفایل انجام نشد.",
                "en": "Profile update failed."
            }

        if error_code in [30, 31, 32]:
            log_critical_event(
                action='profile_update',
                status='failed',
                user_id=user.id,
                error_code=error_code,
                extra={
                    'username': user.username,
                    'errors': str(errors),
                    'ip': get_client_ip(request)
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
        - code 31: Provided email is invalid or already in use.
        - code 32: Provided phone number is invalid or already in use.
        """,
        request_body=ProfileUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=ProfileUpdateResponseSerializer
            ),
            400: "Bad Request (Code 10,30,31,32)",
            401: "Unauthorized",
        }
    )
    def patch(self, request):
        return self.update(request, partial=True)