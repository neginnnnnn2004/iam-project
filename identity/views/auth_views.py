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
    """دریافت IP واقعی کاربر"""
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
        ثبت نام کاربر جدید و دریافت کدهای پشتیبان یک‌بار مصرف

        کدهای خطای اختصاصی این اندپوینت:
        - code 10: اطلاعات ارسالی (فرمت نام کاربری یا پسورد) اشتباه است.
        - code 11: نام کاربری تکراری است.
        - code 12: یک یا چند فیلد اجباری، اصلاً فرستاده نشده‌اند یا خالی ارسال شده‌اند.
        - code 13: رمز عبور وارد شده معتبر نیست.
        - code 14: با این شماره همراه قبلاً ثبت‌نام صورت گرفته است.
        - code 15: با این آدرس ایمیل قبلاً ثبت‌نام صورت گرفته است.
        - code 16: فرمت ایمیل یا شماره تلفن نامعتبر است.
        """,
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
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
                "message": "ثبت نام شما با موفقیت انجام شد. لطفاً کدهای پشتیبان خود را در جایی امن ذخیره کنید.",
                "user": serializer.data,
                "backup_codes": raw_codes
            }, status=status.HTTP_201_CREATED)

        errors = serializer.errors
        error_code = 10
        error_message = "ثبت نام با خطا مواجه شد. لطفاً ورودی‌ها را بررسی کنید."

        is_missing_required = any(
            'required' in str(err) or 'blank' in str(err) or 'null' in str(err)
            for err in errors.values()
        )

        errors = serializer.errors
        error_code = 10
        error_message = "ثبت نام با خطا مواجه شد. لطفاً ورودی‌ها را بررسی کنید."

        is_missing_required = any(
            'required' in str(err) or 'blank' in str(err) or 'null' in str(err)
            for err in errors.values()
        )

        if is_missing_required:
            error_code = 12
            error_message = "یک یا چند فیلد اجباری ارسال نشده است"

        elif 'password' in errors or 'non_field_errors' in errors or 'confirm_password' in errors:
            error_code = 13
            error_message = "رمز عبور وارد شده معتبر نیست یا با تکرار آن مطابقت ندارد"

        elif 'phone' in errors:
            err_str = str(errors['phone']).lower()
            if 'unique' in err_str or 'exist' in err_str:
                error_code = 14
                error_message = "شماره تلفن تکراری است"
            else:
                error_code = 16
                error_message = "فرمت شماره تلفن نامعتبر است"

        elif 'email' in errors:
            err_str = str(errors['email']).lower()
            if 'unique' in err_str:
                error_code = 15
                error_message = "ایمیل تکراری است"
            else:
                error_code = 16
                error_message = "فرمت ایمیل نامعتبر است"

        elif 'username' in errors:
            err_str = str(errors['username']).lower()
            if 'unique' in err_str or 'exist' in err_str:
                error_code = 11
                error_message = "نام کاربری تکراری است"
            else:
                error_code = 10
                error_message = "فرمت نام کاربری اشتباه است"

        if error_code in [11, 13,14, 15]:
            log_critical_event(
                action="register",
                status='failed',
                error_code=error_code,
                extra={
                    'username': request.data.get('username'),
                    'email': request.data.get('email'),
                    'phone': request.data.get('phone'),
                    'error':serializer.errors,
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
        ورود کاربر و دریافت توکن JWT.

        کدهای خطای اختصاصی :
        - code 10: اطلاعات ارسالی (فرمت نام کاربری یا پسورد) ناقص یا اشتباه است.
        - code 20: نام کاربری یا رمز عبور در دیتابیس مطابقت ندارد(یا کاربر حذف شده است).
        - code 21: وضعیت کاربر غیرفعال است (Unverified, Pending, Suspended).
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
                    'error':serializer.errors,
                }
            )
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ورود ناقص یا نامعتبر است.",
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
                "message": "نام کاربری یا رمز عبور اشتباه است.",
                "detail": None
            }, status=status.HTTP_401_UNAUTHORIZED)

        if user.status in ['unverified', 'pending', 'suspended']:
            status_messages = {
                'unverified': "حساب کاربری شما توسط ادمین تایید نشده است",
                'pending': "حساب کاربری شما در انتظار بررسی است",
                'suspended': "حساب کاربری شما مسدود شده است"
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
                "message": status_messages.get(user.status, "وضعیت حساب نامعتبر"),
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
            "message": "وضعیت حساب کاربری شما نامعتبر است.",
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
                'message': 'پروفایل با موفقیت بروزرسانی شد',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        errors = serializer.errors
        if 'password' in errors:
            error_code = 30
            error_message = "رمز عبور وارد شده معتبر نیست"
            # لاگ امنیتی ثبت کن

        elif 'confirm_password' in errors:
            error_code = 30
            error_message = "تکرار رمز عبور معتبر نیست"

        elif 'non_field_errors' in errors:
            # بررسی محتوای non_field_errors برای خطاهای رمز عبور
            non_field_str = str(errors['non_field_errors'])
            if any(keyword in non_field_str for keyword in ['رمز عبور', 'password', 'تطابق']):
                error_code = 30
                error_message = "رمز عبور وارد شده معتبر نیست"
            else:
                error_code = 10
                error_message = "اطلاعات ارسالی نامعتبر است"

            # اولویت 2: خطاهای یکتایی (Duplicate)
        elif 'email' in errors and 'already' in str(errors['email']).lower():
            error_code = 31
            error_message = "ایمیل وارد شده تکراری است"

        elif 'phone' in errors and 'قبلاً ثبت' in str(errors['phone']):
            error_code = 32
            error_message = "شماره تلفن وارد شده تکراری است"

            # اولویت 3: خطاهای فرمت
        elif 'phone' in errors:
            error_code = 32
            error_message = "فرمت شماره تلفن نامعتبر است"

        elif 'email' in errors:
            error_code = 31
            error_message = "فرمت ایمیل نامعتبر است"

            # اولویت 4: سایر خطاها
        else:
            error_code = 10
            error_message = "ویرایش اطلاعات پروفایل انجام نشد."

            # ========== ثبت لاگ‌ها ==========
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
        بروزرسانی جزئی اطلاعات پروفایل کاربر

        کدهای خطای اختصاصی این اندپوینت:
        - code 10: اطلاعات ارسالی نامعتبر یا اشتباه است.
        - code 30: رمز عبور وارد شده معتبر نیست
        - code 31: ایمیل وارد شده نامعتبر یا تکراری است
        - code 32: شماره تلفن وارد شده نامعتبر یا تکراری است
        """,
        request_body=ProfileUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile update successfully",
                schema=ProfileUpdateResponseSerializer
            ),
            400: "Bad Request (Code 10,30,31,32)",
            401: "Unauthorized",
        }
    )
    def patch(self, request):
        return self.update(request, partial=True)