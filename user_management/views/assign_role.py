from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from identity.models import User
from identity.services import log_critical_event
from identity.permissions import IsSuperAdmin

from user_management.serializers.assign_role import (UserRoleUpdateSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# ================== AssignARoleToUsersBySuperAdmin =====================
class AssignUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @swagger_auto_schema(
        operation_description="""
        Assign or change a user's role (promote to admin, demote to regular user, or change guest to regular user) only by superadmin.

        Custom Error Codes:
        - Code 10: Invalid payload or parameters (e.g., self-role change attempt).
        - Code 40: Target user not found or has been soft-deleted.
        """,
        request_body=UserRoleUpdateSerializer,
        responses={
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 40)",
            200: openapi.Response(
                description="Role assigned successfully",
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
        try:
            target_user = User.objects.select_related('role').filter(pk=pk, deleted_at__isnull=True).first()

            if not target_user:
                log_critical_event(
                    action='change_user_role',
                    status_type='error',
                    request=request,
                    user_id=request.user.id,
                    error_code='USER_NOT_FOUND',
                    extra={
                        'target_user_id': pk,
                    },
                )
                return Response({
                    "error_code": 40,
                    "messages": "User not found or deleted / کاربر مورد نظر یافت نشد یا ممکن است حذف شده باشد.",
                    "detail": None
                }, status=status.HTTP_404_NOT_FOUND)

            if target_user == request.user:
                log_critical_event(
                    action='change_user_role',
                    status_type='error',
                    request=request,
                    user_id=request.user.id,
                    error_code='SELF_ROLE_CHANGE_ATTEMPT',
                    extra={
                        'target_user_id': pk,
                    },
                )
                return Response({
                    "error_code": 10,
                    "messages": "You cannot change your own role / شما نمی‌توانید نقش خودتان را تغییر دهید.",
                    "detail": None
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = UserRoleUpdateSerializer(target_user, data=request.data, partial=True)
            if not serializer.is_valid():
                log_critical_event(
                    action='change_user_role',
                    status_type='error',
                    request=request,
                    user_id=request.user.id,
                    error_code='INVALID_ROLE_PAYLOAD',
                    extra={
                        'target_user_id': target_user.id,
                    },
                )
                return Response({
                    "error_code": 10,
                    "messages": "Invalid payload for role assignment / اطلاعات ارسالی برای تغییر نقش معتبر نیست.",
                    "detail": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            print("VALIDATED DATA:", serializer.validated_data)

            old_role_id = target_user.role.id if target_user.role else None
            old_role_title = target_user.role.title if target_user.role else "None"

            updated_user = serializer.save()

            print("UPDATED USER:", updated_user)
            print("UPDATED ROLE:", updated_user.role)

            new_role_id = updated_user.role.id if updated_user.role else None
            new_role_title = updated_user.role.title if updated_user.role else "None"

            log_critical_event(
                action='change_user_role',
                status_type='success',
                request=request,
                user_id=request.user.id,
                extra={
                    'target_user_id': target_user.id,
                    'old_role': {
                        'id': old_role_id,
                        'title': old_role_title,
                    },
                    'new_role': {
                        'id': new_role_id,
                        'title': new_role_title,
                    },
                },
            )

            return Response({
                'message': "User role updated successfully / نقش کاربر با موفقیت بروزرسانی شد.",
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception:
            # logger.exception(
            #     "ROLE_CHANGE_FAILED | TargetUser: %s | Admin: %s",
            #     pk,
            #     request.user.id,
            # )

            log_critical_event(
                action='change_user_role',
                status_type='error',
                request=request,
                user_id=request.user.id,
                error_code='ROLE_CHANGE_FAILED',
                extra={
                    'target_user_id': pk,
                },
            )

            return Response(
                {
                    "detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )