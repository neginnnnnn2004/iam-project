from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import status
from rest_framework.views import APIView

from identity.services import log_critical_event
from identity.models import Group, Domain,UserGroup

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from group_management.serializers.group_domains import (DomainRegisterSerializer)


#  Group Domains List
class GroupDomainView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""
        Get List of Domains Associated with a Specific Group

        Access Levels:

        Admin and Superadmin: Access to domains of all groups

        Regular User and Guest: Can only view domains of groups they are a member of

        Error Codes:
        65: The requested group does not exist or has been deleted
        66: The user does not have access to this group

         """,
        manual_parameters=[
            openapi.Parameter(
                'group_id',
                openapi.IN_PATH,
                description=" (ID) Group",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: DomainRegisterSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden(Code 66)",
            404: "Not Found (Code 65)",
        }
    )
    def get(self, request, group_id):
        action = 'GROUP_DOMAINS_LIST'
        user = request.user

        group = Group.objects.filter(pk=group_id, deleted_at__isnull=True).first()
        if not group:
            log_critical_event(
                action=action,
                status_type='failed',
                request=request,
                user_id=user.id,
                error_code=65,
                extra={'group_id': group_id},
            )
            return Response({
                "error_code": 65,
                "message": {
                    "fa": "گروه مورد نظر یافت نشد.",
                    "en": "The requested group was not found."
                },
            }, status=status.HTTP_404_NOT_FOUND)

        role_code = getattr(user.role, 'code', None)
        is_admin = user.is_superuser or (role_code in ['admin', 'super_admin'])

        if not is_admin:
            is_assigned = UserGroup.objects.filter(user=user, group=group).exists()
            if not is_assigned:
                log_critical_event(
                    action=action,
                    status_type='failed',
                    request=request,
                    user_id=user.id,
                    error_code=66,
                    extra={
                        'group_id': group_id,
                        'role_code': role_code,
                    },
                )
                return Response({
                    "error_code": 66,
                    "message": {
                        "fa": "شما به این گروه دسترسی ندارید.",
                        "en": "You do not have access to this group."
                    },
                }, status=status.HTTP_403_FORBIDDEN)

        domains = Domain.objects.filter(groups=group, deleted_at__isnull=True).distinct()
        serializer = DomainRegisterSerializer(domains, many=True)

        log_critical_event(
            action=action,
            status_type='success',
            request=request,
            user_id=user.id,
            extra={
                'group_id': group_id,
                'access_type': 'admin' if is_admin else 'member',
                'domain_count': domains.count(),
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
