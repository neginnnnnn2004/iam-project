from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone
from rest_framework.views import APIView
from accounts.models import  Group, UserGroup

from accounts.permissions import IsAdminRole
from accounts.serializers.group_serializers import (ListOfGroupsSerializer,
                                                    UserGroupSerializer,
                                                    GroupSerializer,
                                                    GroupCreateSerializer ,
                                                    GroupResponseSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

#1 Group List
class ListOfGroupsView(APIView):
    permission_classes = [IsAuthenticated,IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست گروه ها",
        responses={
            200: ListOfGroupsSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self,request):
        groups = Group.objects.all()
        serializer = ListOfGroupsSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#2 Group Create
class GroupRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="ایجاد گروه جدید",
        request_body=GroupCreateSerializer,
        responses={
            201: GroupResponseSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def post(self, request):
        serializer = GroupCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        group = serializer.save()

        return Response(
            GroupResponseSerializer(group).data,
            status=status.HTTP_201_CREATED
        )

#3 Group Detail, Update, Delete
class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        return get_object_or_404(
            Group.objects.select_related('assigned_by'),
            pk=pk,
            deleted_at__isnull=True
        )

    @swagger_auto_schema(
        operation_description="دریافت جزئیات گروه",
        responses={
            200: GroupSerializer(),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self, request, pk):
        group = self.get_object(pk)
        serializer = GroupSerializer(group)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="ویرایش کامل گروه",
        request_body=GroupSerializer,
        responses={
            200: GroupSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def put(self, request, pk):
        return self.update(request, pk, partial=False)

    @swagger_auto_schema(
        operation_description="ویرایش جزئی گروه",
        request_body=GroupSerializer,
        responses={
            200: GroupSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def patch(self, request, pk):
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial=False):
        group = self.get_object(pk)

        serializer = GroupSerializer(
            group,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="حذف نرم گروه",
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def delete(self, request, pk):
        group = self.get_object(pk)
        group.deleted_at = timezone.now()
        group.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

#4 Assign users to group by admin
class AssignUsersGroups(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="انتساب کاربران به یکی از گروه های موجود توسط ادمین",
        request_body=UserGroupSerializer,
        responses={
            201: openapi.Response(
                description="Assigned successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT
                        )
                    }
                )
            )
        }
    )
    def post(self, request):
        serializer = UserGroupSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user_group = serializer.save(assigned_by=request.user)

        return Response(
            {
                "message": "User assigned to group successfully",
                "data": UserGroupSerializer(user_group).data
            },
            status=status.HTTP_201_CREATED
        )
