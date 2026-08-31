from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import status
from rest_framework.views import APIView

from identity.services import log_critical_event
from identity.permissions import IsAdminRole
from identity.models import Group

from drf_yasg.utils import swagger_auto_schema

from django.utils import timezone

from group_management.serializers.group_detail import (GroupSerializer)


# Group Detail, Update, Delete
class GroupDetailOREditView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        return Group.objects.select_related('assigned_by').filter(pk=pk, deleted_at__isnull=True).first()

    @swagger_auto_schema(
        operation_description="""
        Retrieve the details of a group with admin access.

        Custom error codes:

        code 50: The requested group was not found.
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
            log_critical_event(
                action="GROUP_DETAIL",
                status_type='failed',
                request=request,
                user_id=request.user.id,
                error_code=50,
                extra={
                    'group_id': pk,
                }
            )
            return Response({
                "error_code": 50,
                "message": {
                    "fa": "گروه مورد نظر یافت نشد.",
                    "en": "The requested group was not found."
                },
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = GroupSerializer(group)
        log_critical_event(
            action="GROUP_DETAIL",
            status_type='success',
            request=request,
            user_id=request.user.id,
            extra={
                'group_id': group.id,
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""
        Edit Group with Admin Access

        Specific Error Codes:
        Code 10: The submitted information is invalid.
        Code 50: The requested group was not found.

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
            log_critical_event(
                action="GROUP_UPDATE",
                status_type='failed',
                request=request,
                user_id=request.user.id,
                error_code=50,
                extra={'group_id': pk}
            )
            return Response({
                "error_code": 50,
                "message": {
                    "fa": "گروه مورد نظر جهت ویرایش یافت نشد.",
                    "en": "The group to be edited was not found."
                    },
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = GroupSerializer(group, data=request.data, partial=partial)
        if not serializer.is_valid():
            log_critical_event(
                action="GROUP_DETAIL",
                status_type='failed',
                request=request,
                user_id=request.user.id,
                error_code=10,
                extra={
                    'group_id': group.id,
                    'validation_errors': serializer.errors,
                }
            )
            return Response({
                "error_code": 10,
                "message": {
                    "fa": "اطلاعات ارسالی برای ویرایش  گروه معتبر نیست.",
                    "en": "The submitted information is not valid for editing a group."
                },
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        log_critical_event(
            action="GROUP_UPDATE",
            status_type='success',
            request=request,
            user_id=request.user.id,
            extra={'group_id': group.id}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""
        Soft Delete Group with Admin Access

        Specific Error Codes:

        Code 50: The requested group was not found.
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
            log_critical_event(
                action="GROUP_DELETE",
                status_type='failed',
                request=request,
                user_id=request.user.id,
                error_code=50,
                extra={'group_id': pk}
            )
            return Response({
                "error_code": 50,
                "message": {
                    "fa": "گروه مورد نظر قبلاً حذف شده یا وجود ندارد.",
                    "en": "The requested group has already been deleted or does not exist."
                },
                "detail": None
            }, status=status.HTTP_404_NOT_FOUND)

        group.deleted_at = timezone.now()
        group.save()
        log_critical_event(
            action="GROUP_DELETE",
            status_type='success',
            request=request,
            user_id=request.user.id,
            extra={
                "group_id": group.id,
            }
        )
        return Response(status=status.HTTP_204_NO_CONTENT)