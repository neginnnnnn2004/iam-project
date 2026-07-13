from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone
from rest_framework.views import APIView
from accounts.models import  Group, UserGroup

from accounts.permissions import IsAdminRole
from accounts.serializers.group_serializers import (ListOfGroupsSerializer,UserGroupSerializer,GroupSerializer,GroupCreateSerializer ,GroupResponseSerializer)

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
        operation_description="""
        ایجاد گروه جدید
        
        کدهای خطای اختصاصی :
        - code 10: اطلاعات ارسالی ناقص یا اشتباه است
        """,
        request_body=GroupCreateSerializer,
        responses={
            201: GroupResponseSerializer(),
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def post(self, request):
        serializer = GroupCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ایجاد گروه معتبر نیست.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        group = serializer.save()

        return Response(GroupResponseSerializer(group).data,status=status.HTTP_201_CREATED)

#3 Group Detail, Update, Delete
class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        return Group.objects.select_related('assigned_by').filter(pk=pk,deleted_at__isnull=True).first()

    @swagger_auto_schema(
        operation_description="""
        دریافت جزئیات گروه
        
        کد های اختصاصی:
        - code 50: گروه مورد نظر یافت نشد.
        """,
        responses={
            200: GroupSerializer(),
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 50)",
        }
    )
    def get(self, request, pk):
        group = self.get_object(pk)
        if not group:
            return Response({
                "error_code": 50,
                "message":"گروه مورد نظر یافت نشد یا حذف شده است.",
                "detail":None
            },status=status.HTTP_404_NOT_FOUND)

        serializer = GroupSerializer(group)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""
        ویرایش کامل گروه
        
        کدهای خطای اختصاصی :
        - code 10: اطلاعات ارسالی نامعتبر است.
        - code 50: گروه مورد نظر یافت نشد.
        """,
        request_body=GroupSerializer,
        responses={
            200: GroupSerializer(),
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden (Code 50)",
        }
    )
    def put(self, request, pk):
        return self.update(request, pk, partial=False)

    @swagger_auto_schema(
        operation_description="""
        ویرایش جزئی گروه
        
        کدهای خطای اختصاصی :
        - code 10: اطلاعات ارسالی نامعتبر است.
        - code 50: گروه مورد نظر یافت نشد.
        """,
        request_body=GroupSerializer,
        responses={
            200: GroupSerializer(),
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 50)"
        }
    )
    def patch(self, request, pk):
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial=False):
        group = self.get_object(pk)
        if not group:
            return Response({
                "error_code": 50,
                "message": "گروه مورد نظر جهت ویرایش یافت نشد.",
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = GroupSerializer(group,data=request.data,partial=partial)
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ویرایش گروه معتبر نیست.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""
        حذف نرم گروه
        
        کدهای خطای اختصاصی :
        - code 50: گروه مورد نظر یافت نشد.
        """,
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 50)",
        }
    )
    def delete(self, request, pk):
        group = self.get_object(pk)
        if not group:
            return Response({
                "error_code": 50,
                "message": "گروه مورد نظر قبلاً حذف شده یا وجود ندارد.",
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        group.deleted_at = timezone.now()
        group.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

#4 Assign users to group by admin
class AssignUsersGroups(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="""
        انتساب کاربران به یکی از گروه های موجود توسط ادمین
        
        کدهای خطای اختصاصی :
        - code 10: اطلاعات ارسالی (آیدی کاربر یا گروه) ناقص یا نامعتبر است.
        """,

        request_body=UserGroupSerializer,
        responses={
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
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
        serializer = UserGroupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای انتساب کاربر به گروه معتبر نیست.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user_group = serializer.save(assigned_by=request.user)

        return Response({
                "message": "کاربر با موفقیت به گروه انتساب داده شد.",
                "data": UserGroupSerializer(user_group).data
            },status=status.HTTP_201_CREATED)
