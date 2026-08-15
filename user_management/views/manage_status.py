from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from identity.models import User
from identity.services import log_critical_event
from identity.permissions import IsSuperAdmin

from user_management.serializers.manage_status import (UserStatusUpdateSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone


# ==================  ChangeTheUserStatus&SoftDeleteTheUsersBySuperAdmin =====================
class ManageUsersStatusView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get_object(self, pk):
        return User.objects.filter(pk=pk, deleted_at__isnull=True).first()

    @swagger_auto_schema(
        operation_description="""
        Manage and update user account status only by superadmin (e.g., approving pending users).

        Valid Status Codes:
        - pending: Awaiting approval
        - active: Active / Approved
        - suspended: Suspended
        - unverified: Unverified

        Custom Error Codes:
        - Code 10: Invalid status value supplied in payload.
        - Code 40: Target user not found or soft-deleted.
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
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 40)",
        }
    )
    def patch(self, request, pk):
        try:
            user = self.get_object(pk)
            if not user:
                log_critical_event(
                    action="change_user_status",
                    status_type="error",
                    request=request,
                    user_id=request.user.id,
                    error_code="USER_NOT_FOUND",
                    extra={
                        'target_user_id': pk,
                    }
                )
                return Response({
                    "error_code": 40,
                    "message": "User not found / کاربر مورد نظر یافت نشد.",
                    "detail": None
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = UserStatusUpdateSerializer(user, data=request.data, partial=True)
            if not serializer.is_valid():
                log_critical_event(
                    action="change_user_status",
                    status_type="error",
                    request=request,
                    user_id=request.user.id,
                    error_code="INVALID_STATUS",
                    extra={
                        'target_user_id': pk,
                        'requested_status': request.data.get('status'),
                    }
                )
                return Response({
                    "error_code": 10,
                    "message": "Invalid status option selected / وضعیت انتخاب شده برای کاربر نامعتبر است.",
                    "detail": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            old_status = user.status
            updated_user = serializer.save()
            new_status = updated_user.status

            log_critical_event(
                action="change_user_status",
                status_type="success",
                request=request,
                user_id=request.user.id,
                extra={
                    'target_user_id': user.id,
                    'old_status': old_status,
                    'new_status': new_status,
                }
            )

            return Response({
                "message": f"User status updated successfully to '{new_status}' / وضعیت کاربر با موفقیت به {new_status} تغییر یافت.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception:
            log_critical_event(
                action="change_user_status",
                status_type="error",
                request=request,
                user_id=request.user.id,
                error_code="STATUS_CHANGE_FAILED",
                extra={
                    'target_user_id': pk,
                }
            )
            return Response(
                {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="""
        Soft-delete a user account only by superadmin.

        Custom Error Codes:
        - Code 40: Target user not found or already deleted.
        """,
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 40)",
        }
    )
    def delete(self, request, pk):
        try:
            user = self.get_object(pk)

            if not user:
                log_critical_event(
                    action="soft_delete_user",
                    status_type="error",
                    request=request,
                    user_id=request.user.id,
                    error_code="USER_NOT_FOUND",
                    extra={
                        'target_user_id': pk,
                    }
                )

                return Response({
                    "error_code": 40,
                    "message": "User not found or already deleted / کاربر مورد نظر یافت نشد یا از قبل حذف شده است.",
                    "detail": None
                }, status=status.HTTP_404_NOT_FOUND)

            user.deleted_at = timezone.now()
            user.status = 'deleted'
            user.save()

            log_critical_event(
                action="soft_delete_user",
                status_type="success",
                request=request,
                user_id=request.user.id,
                extra={
                    'target_user_id': user.id,
                }
            )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception:
            log_critical_event(
                action="soft_delete_user",
                status_type="error",
                request=request,
                user_id=request.user.id,
                error_code="SOFT_DELETE_FAILED",
                extra={
                    'target_user_id': pk,
                }
            )
            return Response(
                {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
