from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from django.utils import timezone

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from identity.services import log_critical_event
from identity.permissions import IsAdminRole
from identity.models import Group, UserGroup

from group_management.serializers.group_members import GroupMemberSerializer


class GroupMembersListView(APIView):
    """
    List active members of a group (admin access).
    """

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_group(self, group_id):
        return Group.objects.filter(
            pk=group_id,
            deleted_at__isnull=True
        ).first()

    @swagger_auto_schema(
        operation_description="""
        Retrieve the list of active users assigned to a group (admin access).

        Custom error codes:

        code 65: The requested group does not exist or has been deleted.
        """,
        manual_parameters=[
            openapi.Parameter(
                'group_id',
                openapi.IN_PATH,
                description="Group ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: GroupMemberSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 65)",
        }
    )
    def get(self, request, group_id):

        group = self.get_group(group_id)

        # Group not found
        if not group:
            log_critical_event(
                action="GROUP_MEMBERS_LIST",
                status_type="failed",
                request=request,
                user_id=request.user.id,
                error_code=65,
                extra={
                    "group_id": group_id,
                },
            )

            return Response(
                {
                    "error_code": 65,
                    "message": {
                        "fa": "گروه مورد نظر یافت نشد.",
                        "en": "The requested group was not found."
                    },
                },
                status=status.HTTP_404_NOT_FOUND
            )

        memberships = UserGroup.objects.filter(
            group=group,
            deleted_at__isnull=True
        ).select_related(
            'user',
            'assigned_by'
        )

        member_count = memberships.count()

        serializer = GroupMemberSerializer(
            memberships,
            many=True
        )

        # Successful list
        log_critical_event(
            action="GROUP_MEMBERS_LIST",
            status_type="success",
            request=request,
            user_id=request.user.id,
            extra={
                "group_id": group.id,
                "member_count": member_count,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class GroupMemberDeleteView(APIView):
    """
    Soft-remove a member from a group (admin access).
    """

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_group(self, group_id):
        return Group.objects.filter(
            pk=group_id,
            deleted_at__isnull=True
        ).first()

    @swagger_auto_schema(
        operation_description="""
        Soft-remove a user from a group (admin access).

        Custom error codes:

        code 65: The requested group does not exist or has been deleted.
        code 67: The user is not a member of this group.
        """,
        manual_parameters=[
            openapi.Parameter(
                'group_id',
                openapi.IN_PATH,
                description="Group ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="User ID to remove",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 65 / 67)",
        }
    )
    def delete(self, request, group_id, user_id):

        group = self.get_group(group_id)

        # Group not found
        if not group:
            log_critical_event(
                action="REMOVE_GROUP_MEMBER",
                status_type="failed",
                request=request,
                user_id=request.user.id,
                error_code=65,
                extra={
                    "group_id": group_id,
                    "target_user_id": user_id,
                },
            )

            return Response(
                {
                    "error_code": 65,
                    "message": {
                        "fa": "گروه مورد نظر یافت نشد.",
                        "en": "The requested group was not found."
                    },
                },
                status=status.HTTP_404_NOT_FOUND
            )

        membership = UserGroup.objects.filter(
            group=group,
            user_id=user_id,
            deleted_at__isnull=True
        ).select_related(
            'user'
        ).first()

        # User is not a member
        if not membership:
            log_critical_event(
                action="REMOVE_GROUP_MEMBER",
                status_type="failed",
                request=request,
                user_id=request.user.id,
                error_code=67,
                extra={
                    "group_id": group.id,
                    "target_user_id": user_id,
                },
            )

            return Response(
                {
                    "error_code": 67,
                    "message": {
                        "fa": "این کاربر عضو این گروه نیست.",
                        "en": "This user is not a member of this group."
                    },
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Soft delete membership
        membership.deleted_at = timezone.now()
        membership.save(
            update_fields=['deleted_at']
        )

        # Successful removal
        log_critical_event(
            action="REMOVE_GROUP_MEMBER",
            status_type="success",
            request=request,
            user_id=request.user.id,
            extra={
                "group_id": group.id,
                "target_user_id": user_id,
                "membership_id": membership.id,
            },
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )