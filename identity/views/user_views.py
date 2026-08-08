from rest_framework import status
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.views import APIView

from identity.models import User, Role
from identity.permissions import IsAdminRole, IsSuperAdmin

from identity.serializers.user_serializers import (ListOfUsersSerializer, UserRoleUpdateSerializer,
                                                   listOfRoleSerializer, UserStatusUpdateSerializer,
                                                   UserActivationSerializer, ListOfRoleUsersSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import json
import logger

logger = logger.get_logger('myapp')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def safe_json_sumps(data):
    try:
        return json.dumps(data, ensure_ascii=False)
    except:
        return str(data)


# 1 ListOfAllUsers
class ListOfUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست تمام کاربران با دسترسی ادمین",
        responses={
            200: ListOfUsersSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }

    )
    def get(self, request):
        logger.info("=" * 60)
        logger.info("دریافت لیست تمام کاربران")
        logger.info(f"IP: {get_client_ip(request)}")
        logger.info(f"کاربر درخواست دهنده:{request.user.username} (ID:{request.user.id})")

        users = User.objects.all()
        serializer = ListOfUsersSerializer(users, many=True)
        logger.info(f"تعداد کاربران یافت شده: {users.count()}")
        logger.info("=" * 60)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 2 ListOfAllPendingUsers
class PendingUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست کاربران در انتظار تایید، با دسترسی ادمین",
        responses={
            200: ListOfUsersSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self, request):
        logger.info("=" * 60)
        logger.info("دریافت لیست کاربران در انتظار تایید ")
        logger.info(f"IP: {get_client_ip(request)}")
        logger.info(f"کاربر درخواست‌دهنده: {request.user.username} (ID: {request.user.id})")

        users = User.objects.filter(status="pending")
        serializer = ListOfUsersSerializer(users, many=True)
        logger.info(f"تعداد کاربران در انتظار تایید: {users.count()}")
        logger.info("=" * 60)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 3 ListOfAllRoles
class ListOfRolesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="دریافت لیست نقش ها با دسترسی ادمین",
        responses={
            200: listOfRoleSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self, request):
        logger.info("=" * 60)
        logger.info("دریافت لیست نقش‌ها")
        logger.info(f"IP: {get_client_ip(request)}")
        logger.info(f"کاربر درخواست‌دهنده: {request.user.username} (ID: {request.user.id})")

        role = Role.objects.all()
        serializer = listOfRoleSerializer(role, many=True)

        logger.info(f"تعداد نقش‌ها: {role.count()}")
        logger.info("=" * 60)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 3.1 ReturnMyRole
class ReturnTheRoleOfUser(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="دریافت اطلاعات کامل و نقش کاربر لاگین شده",
        responses={
            200: ListOfRoleUsersSerializer(),
            401: "Unauthorized",
        }
    )
    def get(self, request):
        user = request.user
        serializer = ListOfRoleUsersSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 4 Assign a role to users by admin
class AssignUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @swagger_auto_schema(
        operation_description="""
تغییر و انتساب نقش کاربر (ارتقا به ادمین، تنزل به کاربر عادی، تغییر مهمان به عادی) توسط سوپرادمین        

        کدهای خطای اختصاصی :
        - code 10: اطلاعات ارسالی ناقص یا اشتباه است.
        - code 40: کاربر مورد نظر یافت نشد یا حذف شده است.
        """,
        request_body=UserRoleUpdateSerializer,
        responses={
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 40)",
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
    def patch(self, request, pk):
        logger.info("=" * 60)
        logger.info("شروع فرآیند تغییر نقش کاربر")
        logger.info(f"IP: {get_client_ip(request)}")
        logger.info(f"کاربر درخواست‌دهنده: {request.user.username} (ID: {request.user.id})")
        logger.info(f"نقش کاربر درخواست‌دهنده: {request.user.role.name if request.user.role else 'بدون نقش'}")
        logger.info(f"کاربر هدف (ID): {pk}")

        user = User.objects.select_related('role').filter(pk=pk, deleted_at__isnull=True).first()
        if not user:
            logger.warning(f"کاربر با ID {pk} یافت نشد یا حذف شده است")
            logger.info("=" * 60)
            return Response({
                "error_code": 40,
                "messages": "کاربر مورد نظر یافت نشد یا ممکن است حذف شده باشد.",
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"کاربر هدف پیدا شد::{user.username} (ID: {request.user.id})")
        logger.info(f"نقش فعلی کاربر هدف: {user.role.name if user.role else 'بدون نقش'}")

        logger.info(f"وضعیت کاربر هدف: {user.status}")

        if user == request.user:
            logger.warning(f"تلاش برای تغییر نقش خود توسط کاربر {request.user.username} (ID: {request.user.id})")
            logger.info("=" * 60)
            return Response({
                "error_code": 10,
                "messages": "شما نمی‌توانید نقش خودتان را تغییر دهید.",
                "detail": None
            }, status=status.HTTP_400_BAD_REQUEST)

        requested_role = request.data.get('role', None)
        logger.info(f"نقش درخواستی برای کاربر: {requested_role}")

        serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            logger.warning(f"اطلاعات ارسالی برای تغییر نقش نامعتبر است")
            logger.warning(f"جزئیات خطا: {safe_json_sumps(serializer.errors)}")
            logger.info("=" * 60)

            return Response({
                "error_code": 10,
                "messages": "اطلاعات ارسالی برای تغییر نقش معتبر نیست",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(
            {
                'message': "نقش کاربر با موفقیت بروزرسانی شد.",
                'data': serializer.data
            }, status=status.HTTP_200_OK)


# 5 change the user status
# list of status:[unverified,pending,active,suspended,deleted]

class ManageUsersStatusView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get_object(self, pk):
        return User.objects.filter(pk=pk, deleted_at__isnull=True).first()

    @swagger_auto_schema(
        operation_description="""
مدیریت و تغییر وضعیت کاربر توسط سوپرادمین (از جمله تایید حساب‌های کاربری در انتظار تایید)        

        کدهای وضعیت معتبر:
        - pending: در انتظار تایید
        - active: فعال / تایید شده 
        - suspended: معلق
        - unverified: تایید نشده

        کدهای خطای اختصاصی :
        - code 10: وضعیت ارسالی نامعتبر است.
        - code 40: کاربر مورد نظر یافت نشد.
        """,
        request_body=UserStatusUpdateSerializer,
        responses={
            200: openapi.Response(
                description="User status updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: "Bad Request (Code 10)",
            404: "Not Found (Code 40)",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def patch(self, request, pk):
        logger.info("=" * 60)
        logger.info("شروع فرآیند تغییر وضعیت کاربر")
        logger.info(f"IP: {get_client_ip(request)}")
        logger.info(f"کاربر درخواست‌دهنده: {request.user.username} (ID: {request.user.id})")
        logger.info(f"نقش کاربر درخواست‌دهنده: {request.user.role.name if request.user.role else 'بدون نقش'}")
        logger.info(f"کاربر هدف (ID): {pk}")

        requested_status = request.data.get('status', 'نامشخص')
        logger.info(f"وضعیت درخواستی: {requested_status}")

        user = self.get_object(pk)
        if not user:
            logger.warning(f"کاربر با ID {pk} یافت نشد یا حذف شده است")
            logger.info("=" * 60)

            return Response({
                "error_code": 40,
                "message": "کاربر مورد نظر یافت نشد.",
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"کاربر هدف پیدا شد: {user.username} (ID: {user.id})")
        logger.info(f"وضعیت فعلی کاربر: {user.status}")
        logger.info(f"ایمیل: {user.email}")
        logger.info(f"شماره تلفن: {user.phone}")

        serializer = UserStatusUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            logger.warning(f"وضعیت ارسالی نامعتبر است")
            logger.warning(f"جزئیات خطا: {json.dumps(serializer.errors)}")
            logger.info("=" * 60)

            return Response({
                "error_code": 10,
                "message": "وضعیت انتخاب شده برای کاربر نامعتبر است.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        update_user = serializer.save()
        logger.info(f"وضعیت کاربر {user.username} با موفقیت تغییر یافت")
        logger.info(f"وضعیت قبلی: {user.status}")
        logger.info(f"وضعیت جدید: {update_user.status}")
        logger.info(f"تغییر توسط: {request.user.username} (ID: {request.user.id})")
        logger.info("=" * 60)

        return Response({
            "message": f"وضعیت کاربر با موفقیت به {update_user.status} تغییر یافت.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""
        حذف نرم کاربر با دسترسی سوپرادمین

        کدهای خطای اختصاصی :
        - code 40: کاربر مورد نظر یافت نشد.
        """,
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 40)",
        }
    )
    def delete(self, request, pk):
        logger.info("=" * 60)
        logger.info("شروع فرآیند حذف نرم کاربر")
        logger.info(f"IP: {get_client_ip(request)}")
        logger.info(f"کاربر درخواست‌دهنده: {request.user.username} (ID: {request.user.id})")
        logger.info(f"نقش کاربر درخواست‌دهنده: {request.user.role.name if request.user.role else 'بدون نقش'}")
        logger.info(f"کاربر هدف (ID): {pk}")

        user = self.get_object(pk)
        if not user:
            logger.warning(f"کاربر با ID {pk} یافت نشد یا از قبل حذف شده است")
            logger.info("=" * 60)
            return Response({
                "error_code": 40,
                "message": "کاربر مورد نظر یافت نشد؛ یا از قبل حذف شده است.",
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"کاربر هدف پیدا شد: {user.username} (ID: {user.id})")
        logger.info(f"وضعیت فعلی کاربر: {user.status}")
        logger.info(f"ایمیل: {user.email}")
        logger.info(f"شماره تلفن: {user.phone}")

        user.deleted_at = timezone.now()
        user.status = 'deleted'
        user.save()

        logger.info(f"کاربر {user.username} (ID: {user.id}) با موفقیت حذف شد (حذف نرم)")
        logger.info(f"تاریخ حذف: {user.deleted_at}")
        logger.info(f"تغییر توسط: {request.user.username} (ID: {request.user.id})")
        logger.info("=" * 60)
        return Response(status=status.HTTP_204_NO_CONTENT)


# 6 make user active or inactive
class UserActivationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="""
        فعال یا غیرفعال کردن کاربر با دسترسی ادمین

        کدهای خطای اختصاصی :
        - code 10: مقدار فرستاده شده برای فیلد is_active نامعتبر است.
        - code 40: کاربر مورد نظر یافت نشد.
        """,
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
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 40)",
        }
    )
    def patch(self, request, pk):
        logger.info("=" * 60)
        logger.info("شروع فرآیند فعال/ غیر فعال کردن کاربر")
        logger.info(f"IP: {get_client_ip(request)}")
        logger.info(f"کاربر درخواست‌دهنده: {request.user.username} (ID: {request.user.id})")
        logger.info(f"کاربر هدف (ID): {pk}")
        user = User.objects.filter(pk=pk, deleted_at__isnull=True).first()
        if not user:
            logger.warning(f"کاربر با ID {pk} یافت نشد یا حذف شده است")
            logger.info("=" * 60)
            return Response({
                "error_code": 40,
                "message": "کاربر مورد نظر یافت نشد.",
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"کاربر هدف پیدا شد: {user.username} (ID: {user.id})")
        logger.info(f"وضعیت فعال یا غیرفعال بودن فعلی کاربر: {user.is_active}")
        serializer = UserActivationSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"وضعیت ارسال نامعتبر است")
            logger.warning(f"جزئیات خطا: {json.dumps(serializer.errors)}")
            logger.info("=" * 60)
            return Response({
                "error_code": 10,
                "message": "اطلاعات فرستاده شده برای فعال‌سازی معتبر نیست.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = serializer.validated_data['is_active']
        user.save(update_fields=['is_active'])

        logger.info(f"وضعیت فعال بودن یا نبودن کاربر {user.username} با موفقیت تغییر یافت")
        logger.info(f"وضعیت قبلی: {user.is_active}")
        logger.info(f"وضعیت جدید: {user.is_active}")
        logger.info(f"تغییر توسط: {request.user.username} (ID: {request.user.id})")
        logger.info("=" * 60)
        return Response({
            "message": "وضعیت کاربر تغییر کرد",
            "is_active": user.is_active
        }, status=status.HTTP_200_OK)