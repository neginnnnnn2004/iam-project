from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import status
from rest_framework.views import APIView

from identity.services import log_critical_event
from identity.permissions import IsAdminRole

from drf_yasg.utils import swagger_auto_schema

from group_management.serializers.group_register import (GroupCreateSerializer, GroupResponseSerializer)


#  Group Create
class GroupRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="""
        Create a new group with admin access.

        Custom error codes:

        code 10: The submitted information is incomplete or incorrect.

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
            log_critical_event(
                action="group_register",
                status_type='failed',
                request=request,
                user_id=request.user.id,
                error_code=10,
                extra={
                    'validation_errors': serializer.errors,
                }
            )
            return Response({
                "error_code": 10,
                "message": {
                    "fa": "اطلاعات ارسالی برای ایجاد گروه معتبر نیست.",
                    "en": "The submitted information is not valid for creating a group."
                },
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        group = serializer.save()

        log_critical_event(
            action="group_register",
            status_type='success',
            request=request,
            user_id=request.user.id,
            extra={
                "group_id": group.id,
                "group_name": getattr(group, 'name',None),
            }
        )
        return Response(GroupResponseSerializer(group).data, status=status.HTTP_201_CREATED)