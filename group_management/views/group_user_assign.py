from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import status
from rest_framework.views import APIView

from identity.services import log_critical_event
from identity.permissions import IsAdminRole

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from group_management.serializers.group_assign_users import (UserGroupSerializer)


# Assign users to group by admin
class AssignUsersGroups(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="""
        Assign Users to an Existing Group by Admin

        Specific Error Codes:

        Code 10: The submitted information (user ID or group ID) is incomplete or invalid.
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
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    )
    def post(self, request):
        serializer = UserGroupSerializer(data=request.data)
        if not serializer.is_valid():
            log_critical_event(
                action="GROUP_ASSIGN_USERS",
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
                    "fa": "اطلاعات ارسالی برای انتساب کاربر به گروه معتبر نیست.",
                    "en": "The submitted information for assigning the user to the group is invalid."
                },
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user_group = serializer.save(assigned_by=request.user)
        log_critical_event(
            action="GROUP_ASSIGN_USERS",
            status_type='success',
            request=request,
            user_id=request.user.id,
            extra={
                'user_group_id': user_group.id,
                'user_id': user_group.user_id,
                'group_id': user_group.group_id,
            }
        )
        return Response({
            "message": {
                "fa": "کاربر با موفقیت به گروه انتساب داده شد.",
                "en": "The user was successfully assigned to the group."
            },
             "data": UserGroupSerializer(user_group).data
        }, status=status.HTTP_201_CREATED)