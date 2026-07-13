from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from identity.serializers.auth_serializers import (UserRegisterSerializer,UserLoginSerializer,ProfileUpdateSerializer,ProfileUpdateResponseSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# 1 registration
class UserRegisterView(APIView):
    @swagger_auto_schema(
        operation_description="""
        ثبت نام کاربر جدید

        کدهای خطای اختصاصی  :
        - code 10: اطلاعات ارسالی (فرمت نام کاربری یا پسورد) اشتباه است.
        - code 11: نام کاربری تکراری است .
        - code 12: یک یا چند فیلدِ اجباری، اصلاً فرستاده نشده‌اند یا خالی ارسال شده‌اند.
        """,
        request_body=UserRegisterSerializer,
        responses={
            201: UserRegisterSerializer,
            400: "Bad Request(Code 10 or 11 or 12)",
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        errors = serializer.errors
        error_code = 10

        error_string = str(errors)

        if 'required' in error_string or 'blank' in error_string:
            error_code = 12
        elif 'unique' in error_string and 'username' in errors:
            error_code = 11

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
        return Response({
            "error_code": 10,
            "message": "ویرایش اطلاعات پروفایل انجام نشد.",
            "detail": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""
        بروزرسانی کامل پروفایل کاربر
        کدهای خطای اختصاصی این اندپوینت :
        - code 10: اطلاعات ارسالی (فرمت نام کاربری یا پسورد) ناقص یا اشتباه است.
        """,
        request_body=ProfileUpdateSerializer,
        responses={
            200: ProfileUpdateResponseSerializer,
            401: "Unauthorized",
            400: "Bad Request (Code 10)",
        }
    )
    def put(self, request):
        return self.update(request, partial=False)

    @swagger_auto_schema(
        operation_description="بروزرسانی جزیی پروفایل کاربر",
        request_body=ProfileUpdateSerializer,
        responses={
            200: ProfileUpdateResponseSerializer,
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
        }
    )
    def patch(self, request):
        return self.update(request, partial=True)