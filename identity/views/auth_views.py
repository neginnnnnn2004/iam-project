from django.contrib.auth import authenticate
import json
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from identity.serializers.auth_serializers import (UserRegisterSerializer,UserLoginSerializer,ProfileUpdateSerializer,ProfileUpdateResponseSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from identity.utils import create_user_backup_codes

from typing import Optional
from identity.models import User

import logging

logger = logging.getLogger('myapp')

# ================== help full def =====================
def get_client_ip(request):
    """دریافت IP واقعی کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def safe_json_dumps(data):
    """تبدیل به JSON با مدیریت خطا"""
    try:
        return json.dumps(data, ensure_ascii=False)
    except:
        return str(data)

# 1 registration
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
            400: "Bad Request (Code 10,11,12,13,14,15)",
        }
    )
    def post(self, request):
        logger.info("=" * 60)
        logger.info(f"شروع فرآیند ثبت نام کاربر جدید")
        logger.info(f" IP: {get_client_ip(request)}")
        logger.info(f" User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}")

        safe_data = {k: v for k, v in request.data.items() if k != 'password' and k != 'confirm_password'}
        logger.info(f"اطلاعات ثبت نام: {safe_json_dumps(safe_data)}")

        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            logger.info(f" اطلاعات ثبت نام معتبر است")

            user = serializer.save()
            raw_codes = create_user_backup_codes(user, count=8)
            logger.info(f" کاربر جدید ایجاد شد: ID={user.id}, Username={user.username}")
            logger.info(f"Email: {user.email}")
            logger.info(f"Phone: {user.phone}")
            logger.info(f"{len(raw_codes)}کد پشتیبان ایجاد شد ")

            user_data = serializer.data
            user_data.pop('confirm_password', None)
            logger.info(" ثبت نام با موفقیت کامل شد")
            logger.info("=" * 60)

            return Response({
                "message": "ثبت نام شما با موفقیت انجام شد. لطفاً کدهای پشتیبان خود را در جایی امن ذخیره کنید.",
                "user": serializer.data,
                "backup_codes": raw_codes
            }, status=status.HTTP_201_CREATED)

        errors = serializer.errors
        error_code = 10

        is_missing_required = any(
            'required' in str(err) or 'blank' in str(err) or 'null' in str(err)
            for err in errors.values()
        )

        if  is_missing_required:
            error_code = 12
            logger.warning(f" فیلدهای اجباری ارسال نشده: {list(errors.keys())}")

        elif 'phone' in errors:
            error_code = 14
            logger.warning(f"شماره تلفن تکراری یا نامعتبر: {request.data.get('phone')}")

        elif 'email' in errors:
            error_code = 15
            logger.warning(f" ایمیل تکراری یا نامعتبر: {request.data.get('email')}")

        elif 'username' in errors:
            err_str = str(errors['username']).lower()
            if 'unique' in err_str or 'exist' in err_str:
                error_code = 11
                logger.warning(f" نام کاربری تکراری: {request.data.get('username')}")
            else:
                error_code = 10
                logger.warning(f" فرمت نام کاربری اشتباه: {errors['username']}")


        elif 'password' in errors or 'confirm_password' in errors or 'non_field_errors' in errors:
            error_code = 13
            logger.warning(f" خطا در رمز عبور: {errors}")

        logger.error(f" ثبت نام ناموفق - Error Code: {error_code}")
        logger.error(f" جزئیات خطا: {safe_json_dumps(errors)}")
        logger.info("=" * 60)

        return Response({
            "error_code": error_code,
            "message": "ثبت نام با خطا مواجه شد. لطفاً ورودی‌ها را بررسی کنید.",
            'detail': errors
        }, status=status.HTTP_400_BAD_REQUEST)


# 2 Login
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
            401: "Unauthorized (Code 20 /  Code 21)",
            400: "Bad Request (Code 10)",
        }
    )
    def post(self, request):
        logger.info("=" * 60)
        logger.info(f" تلاش برای ورود کاربر")
        logger.info(f" IP: {get_client_ip(request)}")
        logger.info(f" Username: {request.data.get('username', 'unknown')}")

        serializer = UserLoginSerializer(data=request.data)
        # check the fields
        if not serializer.is_valid():
            logger.warning(f" اطلاعات ورود ناقص یا نامعتبر: {serializer.errors}")
            logger.info("=" * 60)

            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ورود ناقص یا نامعتبر است.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # user authenticate with help of (authenticate method)
        user : Optional[User] = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        # if user not found
        if user is None or user.status == 'deleted':
            logger.warning(f" تلاش ناموفق برای ورود - کاربر یافت نشد: {serializer.validated_data['username']}")
            logger.warning(f" IP: {get_client_ip(request)}")
            logger.info("=" * 60)

            return Response({
                "error_code": 20,
                "message": "نام کاربری یا رمز عبور اشتباه است.",
                "detail": None
            }, status=status.HTTP_401_UNAUTHORIZED)
        logger.info(f" کاربر پیدا شد: ID={user.id}, Username={user.username}, Status={user.status}")

        if user.status in ['unverified', 'pending', 'suspended']:
            status_messages = {
                'unverified': "حساب کاربری شما توسط ادمین تایید نشده است",
                'pending': "حساب کاربری شما در انتظار بررسی است",
                'suspended': "حساب کاربری شما مسدود شده است"
            }

            logger.warning(f" تلاش برای ورود کاربر با وضعیت {user.status}: {user.username}")
            logger.info("=" * 60)

            return Response({
                "error_code": 21,
                "message": status_messages.get(user.status, "وضعیت حساب نامعتبر"),
                "detail": None
            },status=status.HTTP_401_UNAUTHORIZED)


        # create token
        elif user.status == 'active':
            refresh = RefreshToken.for_user(user)
            logger.info(f" ورود موفق کاربر: {user.username} (ID: {user.id})")
            logger.info("=" * 60)

            return Response({
                'access_token': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)

        logger.error(f" وضعیت نامشخص برای کاربر: {user.username}, Status: {user.status}")
        logger.info("=" * 60)
        return Response({
            "error_code": 21,
            "message": "وضعیت حساب کاربری شما نامعتبر است.",
            "detail": None
        }, status=status.HTTP_401_UNAUTHORIZED)


# 3 ProfileUpdate
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, partial=False):
        user = request.user

        logger.info("=" * 60)
        logger.info("️ شروع بروزرسانی پروفایل")
        logger.info(f" کاربر: {user.username} (ID: {user.id})")
        logger.info(f" IP: {get_client_ip(request)}")
        logger.info(f" متد: {'PATCH' if partial else 'PUT'}")

        safe_data = {k: v for k, v in request.data.items() if k != 'password'}
        logger.info(f" داده‌های جدید: {safe_json_dumps(safe_data)}")

        serializer = ProfileUpdateSerializer(
            instance=user,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()
            changed_fields = list(request.data.keys())
            logger.info(f" پروفایل {user.username} با موفقیت بروزرسانی شد")
            logger.info(f" فیلدهای تغییر یافته: {changed_fields}")
            logger.info("=" * 60)
            return Response({
                'message': 'پروفایل با موفقیت بروزرسانی شد',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        errors = serializer.errors
        error_code = 10

        if 'password' in errors:
            error_code = 30
            logger.warning(f" خطا در رمز عبور")

        logger.error(f" بروزرسانی پروفایل ناموفق - Error Code: {error_code}")
        logger.error(f" جزئیات خطا: {safe_json_dumps(errors)}")
        logger.info("=" * 60)

        return Response({
            "error_code":  error_code,
            "message": "ویرایش اطلاعات پروفایل انجام نشد.",
            "detail": errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""
                بروزرسانی جزئی اطلاعات پروفایل کاربر

                کدهای خطای اختصاصی این اندپوینت:
                - code 10: اطلاعات ارسالی نامعتبر یا اشتباه است.
                - code 30: رمز عبور وارد شده معتبر نیست؛ رمز عبور باید شامل حداقل ۸ کاراکتر به صورت ترکیبی از اعداد و حروف باشد، از رمزهای ساده و رایج استفاده نشود و شبیه نام کاربری یا ایمیل نباشد.
                """,

        request_body=ProfileUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile update successfully",
                schema=ProfileUpdateSerializer
            ),
            400: "Bad Request (Code 10,30)",
            401: "Unauthorized",
        }
    )
    def patch(self, request):
        return self.update(request, partial=True)