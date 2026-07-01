from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.views import APIView

from accounts.models import User, Role
from accounts.permissions import IsAdminRole

from accounts.serializers.user_serializers import (ListOfUsersSerializer,
                                                   UserRoleUpdateSerializer,
                                                   listOfRoleSerializer,
                                                   UserStatusUpdateSerializer ,
                                                   UserActivationSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

#1 ListOfAllUsers
class ListOfUsersView(APIView):
    @swagger_auto_schema(
        operation_description="دریافت لیست تمام کاربران",
        responses={200:ListOfUsersSerializer(many=True)}
    )
    def get(self,request):
        users = User.objects.all()
        serializer = ListOfUsersSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#2 ListOfAllPendingUsers
class PendingUsersView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست کاربران در انتظار تایید" ,
        responses={
            200: ListOfUsersSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self,request):
        users = User.objects.filter(status="pending")
        serializer = ListOfUsersSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#3 ListOfAllRoles
class ListOfRolesView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست نقش ها",
        responses={
            200: listOfRoleSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )

    def get(self,request):
        role = Role.objects.all()
        serializer = listOfRoleSerializer(role, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#4 Assign a role to users by admin
class AssignUserRoleView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    @swagger_auto_schema(
        operation_description="انتساب یک نقش از نقش های موجود به کاربر مورد نظر توسط ادمین",
        request_body=UserRoleUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Assigned successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            )
        }
    )

    def patch(self,request,pk ):
        user = get_object_or_404(User,pk=pk,deleted_at__isnull=True)

        serializer = UserRoleUpdateSerializer(
            user,
            data=request.data ,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'message':"نقش کاربر با موفقیت بروزرسانی شد." ,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

#5 change the user status
#list of status:[unverified,pending,active,suspended,deleted]

class ManageUsersStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk, deleted_at__isnull=True)

    @swagger_auto_schema(
        operation_description="تغییر وضعیت کاربر",
        request_body=UserStatusUpdateSerializer,
        responses={
            200: openapi.Response(
                description="User status updated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: "Bad Request",
        }
    )

    def patch(self, request, pk):
        user = self.get_object(pk)

        serializer = UserStatusUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        update_user = serializer.save()

        return Response(
            {
                "message": f"وضعیت کاربر با موفقیت به {update_user.status} تغییر یافت.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="حذف نرم کاربر",
        responses={
            204: "No Content",
            401:"Unauthorized",
            403:"Forbidden",
        }
    )
    def delete(self, request, pk):
        user = self.get_object(pk)
        user.deleted_at = timezone.now()
        user.status = 'deleted'
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

#6 make user active or inactive
class UserActivationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="فعال یا غیرفعال کردن کاربر",
        request_body=UserActivationSerializer,
        responses={
            200: openapi.Response(
                description="activation changed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk, deleted_at__isnull=True)

        serializer = UserActivationSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user.is_active = serializer.validated_data['is_active']
        user.save(update_fields=['is_active'])

        return Response(
            {
                "message": "وضعیت کاربر تغییر کرد",
                "is_active": user.is_active
            },
            status=status.HTTP_200_OK
        )