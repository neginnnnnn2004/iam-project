from typing import Optional

from django.contrib.auth import authenticate
from rest_framework import status

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from identity.models import User
from accounts.serializers.login import (UserLoginSerializer,)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from identity.services import log_critical_event
# ================== Login =====================
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

        normalized_username = serializer.validated_data['username'].strip().lower()

        user: Optional[User] = authenticate(
            username=normalized_username,
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