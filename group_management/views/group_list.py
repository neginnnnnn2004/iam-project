from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import status
from identity.services import log_critical_event

from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from identity.models import Group, UserGroup
from group_management.serializers.group_list import (AdminListOfGroupsSerializer, UserListOfGroupsSerializer,)


#  Group List
class ListOfGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the list of groups for any authenticated user. Regular users and guests see only the groups they belong to, while admins see all groups.",
        responses={
            200: UserListOfGroupsSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def get(self, request):
        action = 'GROUP_LIST'
        user = request.user

        is_admin = (
                user.is_superuser or
                (user.role is not None and user.role.code in ['admin', 'super_admin'])
        )

        try:
            active_groups = Group.objects.filter(deleted_at__isnull=True)

            if is_admin:
                groups = active_groups.annotate(
                    user_count=Count(
                        'group_memberships',
                        filter=Q(group_memberships__deleted_at__isnull=True),
                        distinct=True
                    ),
                    tags_count=Count(
                        'domains__user_domain_tag',
                        filter=Q(domains__user_domain_tag__deleted_at__isnull=True),
                        distinct=True
                    )
                )
                serializer = AdminListOfGroupsSerializer(groups, many=True)
                access_type = 'admin'
            else:
                user_group_ids = UserGroup.objects.filter(
                    user=user,
                    deleted_at__isnull=True
                ).values_list('group_id', flat=True)

                groups = active_groups.filter(id__in=user_group_ids).distinct()
                serializer = UserListOfGroupsSerializer(groups, many=True)
                access_type = 'member'

            log_critical_event(
                action="list_of_groups",
                status_type='success',
                request=request,
                user_id=user.id,
                extra={
                    'access_type': access_type,
                    'group_count': groups.count(),
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            log_critical_event(
                action="list_of_groups",
                status_type='error',
                request=request,
                user_id=user.id,
                error_code=500,
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                }
            )
            return Response(
                {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
