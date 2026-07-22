from idlelib.iomenu import errors

from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from identity.serializers.auth_serializers import (UserRegisterSerializer,UserLoginSerializer,ProfileUpdateSerializer,ProfileUpdateResponseSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from identity.utils import create_user_backup_codes

# 1 registration
class UserRegisterView(APIView):
    @swagger_auto_schema(
        operation_description="""
        ثبت نام کاربر جدید و دریافت کدهای پشتیبان یک‌بار مصرف

        کدهای خطای اختصاصی این اندپوینت:
        - code 10: اطلاعات ارسالی (فرمت نام کاربری یا پسورد) اشتباه است.
        - code 11: نام کاربری تکراری است.
        - code 12: یک یا چند فیلد اجباری، اصلاً فرستاده نشده‌اند یا خالی ارسال شده‌اند.
        - code 14: رمز عبور وارد شده معتبر نیست؛ رمز عبور باید شامل حداقل ۸ کاراکتر به صورت ترکیبی از اعداد و حروف باشد، از رمزهای ساده و رایج استفاده نشود و شبیه نام کاربری یا ایمیل نباشد.
        - code 15: با این شماره همراه قبلاً ثبت‌نام صورت گرفته است.
        - code 16: با این آدرس ایمیل قبلاً ثبت‌نام صورت گرفته است.
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
            400: "Bad Request (Code 10,11,12,14,15,16)",
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            raw_codes = create_user_backup_codes(user, count=8)

            return Response({
                "message": "ثبت نام شما با موفقیت انجام شد. لطفاً کدهای پشتیبان خود را در جایی امن ذخیره کنید.",
                "user": serializer.data,
                "backup_codes": raw_codes
            }, status=status.HTTP_201_CREATED)

        errors = serializer.errors
        error_code = 10

        is_missing_required = False
        for field, field_errors in errors.items():
            err_str  = str(field_errors)
            if 'required' in err_str or 'blank' in err_str or 'null' in err_str:
                is_missing_required = True
                break

        if  is_missing_required:
            error_code = 12
        elif 'phone' in errors:
            error_code = 15
        elif 'email' in errors:
            error_code = 16
        elif 'username' in errors:
            err_str = str(errors['username']).lower()
            if 'unique' in err_str or 'exist' in err_str:
                error_code = 11
            else:
                error_code = 10
        elif 'password' in errors:
            error_code = 14

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
        - code 13: نام کاربری یا رمز عبور در دیتابیس مطابقت ندارد.
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
            401: "Unauthorized (Code 13)",
            400: "Bad Request (Code 10)",
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        # check the fields
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ورود ناقص یا نامعتبر است.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # user authenticate with help of (authenticate method)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        # if user not found
        if user is None:
            return Response({
                "error_code": 13,
                "message": "نام کاربری یا رمز عبور اشتباه است.",
                "detail": None
            }, status=status.HTTP_401_UNAUTHORIZED
            )
        # create token
        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


# 3 ProfileUpdate
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
            return Response({
                'message': 'پروفایل با موفقیت بروزرسانی شد',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        errors = serializer.errors
        error_code = 10
        if 'password' in errors:
            error_code = 14

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
                - code 14: رمز عبور وارد شده معتبر نیست؛ رمز عبور باید شامل حداقل ۸ کاراکتر به صورت ترکیبی از اعداد و حروف باشد، از رمزهای ساده و رایج استفاده نشود و شبیه نام کاربری یا ایمیل نباشد.
                """,

        request_body=ProfileUpdateSerializer,
        responses={
            200: ProfileUpdateResponseSerializer,
            400: "Bad Request (Code 10,14)",
            401: "Unauthorized",
        }
    )
    def patch(self, request):
        return self.update(request, partial=True)