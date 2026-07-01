from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from accounts.serializers.auth_serializers import (UserRegisterSerializer,
                                                   UserLoginSerializer,
                                                   ProfileUpdateSerializer ,
                                                   ProfileUpdateResponseSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

#1 registration
class UserRegisterView(APIView):
    @swagger_auto_schema(
        operation_description="ثبت نام کاربر جدید",
        request_body=UserRegisterSerializer,
        responses={
            201: UserRegisterSerializer,
            400: "Bad Request"
        }
    )
    def post(self,request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#2 Login
class UserLoginView(APIView):
    @swagger_auto_schema(
        operation_description="ورود کاربر و دریافت توکن JWT",
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
            401: "Unauthorized",
            400: "Bad Request"
        }
    )
    def post(self,request):
        serializer = UserLoginSerializer(data=request.data)
        #check the fields
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #user authenticate with help of (authenticate method)
        user = authenticate(
            username = serializer.validated_data['username'],
            password = serializer.validated_data['password']
        )
        #if user not found
        if user is None:
            return Response(
                {"detail":"نام کاربری یا رمز عبور اشتباه است"} ,
                status=status.HTTP_401_UNAUTHORIZED
            )
        #create token
        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh': str(refresh),
        },status=status.HTTP_200_OK)

#3 ProfileUpdate
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
            },status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="بروزرسانی کامل پروفایل کاربر",
        request_body=ProfileUpdateSerializer,
        responses={
            200: ProfileUpdateResponseSerializer,
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def put(self, request):
        return self.update(request, partial=False)

    @swagger_auto_schema(
        operation_description="بروزرسانی جزیی پروفایل کاربر" ,
        request_body=ProfileUpdateSerializer,
        responses={
            200: ProfileUpdateResponseSerializer,
            400: "BAD REQUEST",
            401:"Unauthorized",
        }
    )

    def patch(self, request):
        return self.update(request, partial=True)