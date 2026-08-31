from collections import defaultdict

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import status
from rest_framework.views import APIView

from identity.services import log_critical_event
from identity.models import (Group, Domain, UserGroup, User_Domain_Tag)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from group_management.serializers.group_domains import (DomainRegisterSerializer)
from domain_tag_management.serializers.domain_list import (TagListSerializer)


#  Group Domains List
class GroupDomainView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""
          Get List of Domains Associated with a Specific Group

          Access Levels:

          Admin and Superadmin: Access to domains of all groups

          Regular User and Guest: Can only view domains of groups they are a member of

          Tag Visibility:

          Admin and Superadmin:
          Can see all tags and can add tags. Also receive a per-tag
          breakdown ('tags_overview') listing which users applied
          each tag.

          Limited:
          Can only see main tags and cannot add tags.

          Regular User:
          If a main tag exists, can only see main tags and cannot add tags.

          If no main tag exists, can see their own tags and can add a tag
          if they do not already have one.

          Error Codes:
          65: The requested group does not exist or has been deleted
          66: The user does not have access to this group
          """,
        manual_parameters=[
            openapi.Parameter(
                'group_id',
                openapi.IN_PATH,
                description="(ID) Group",
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

        # Find Group

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

        # Access Control

        role_code = getattr(user.role, 'code', None)
        is_admin = user.is_superuser or (role_code in ['admin', 'super_admin'])
        is_limited = role_code == 'limited'

        if not is_admin:
            is_assigned = UserGroup.objects.filter(
                user=user,
                group=group,
                deleted_at__isnull=True
            ).exists()

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

        # Get Domains

        domains = Domain.objects.filter(groups=group, deleted_at__isnull=True).distinct()
        result = []

        # Domain + Tag Visibility

        for domain in domains:
            domain_tags_qs = User_Domain_Tag.objects.filter(
                domain=domain,
                deleted_at__isnull=True
            ).select_related('tag', 'user__role')

            main_tags = [
                udt.tag
                for udt in domain_tags_qs
                if udt.tag
                   and udt.user.role
                   and udt.user.role.code in ['admin', 'super_admin']
            ]
            has_main_tag = len(main_tags) > 0

            # Current user's tags
            user_tags = [
                udt.tag
                for udt in domain_tags_qs
                if udt.user == user
            ]
            has_user_tag = len(user_tags) > 0

            # Visibility Logic
            if is_admin:
                visible_tags = [udt.tag for udt in domain_tags_qs]
                can_add_tag = True
            elif is_limited:
                visible_tags = main_tags
                can_add_tag = False
            elif has_main_tag:
                visible_tags = main_tags
                can_add_tag = False
            else:
                unique_tags_dict = {
                    tag.id: tag
                    for tag in (main_tags + user_tags)
                }
                visible_tags = list(unique_tags_dict.values())
                can_add_tag = not has_user_tag

            # Serialize Domain
            domain_data = DomainRegisterSerializer(domain).data
            domain_data['tags'] = TagListSerializer(visible_tags, many=True).data
            domain_data['can_add_tag'] = can_add_tag
            domain_data['has_main_tag'] = has_main_tag

            # ---- Admin-only: raw per-tag breakdown with user list ----
            if is_admin:
                tag_groups = defaultdict(list)
                for udt in domain_tags_qs:
                    tag_groups[udt.tag].append(udt.user)

                domain_data['tags_overview'] = [
                    {
                        "tag": TagListSerializer(tag).data,
                        "count": len(users),
                        "users": [
                            {
                                "id": u.id,
                                "username": u.username,
                                "first_name": u.first_name,
                                "last_name": u.last_name,
                            }
                            for u in users
                        ]
                    }
                    for tag, users in tag_groups.items()
                ]

            result.append(domain_data)

        # Logging
        log_critical_event(
            action=action,
            status_type='success',
            request=request,
            user_id=user.id,
            extra={
                'group_id': group_id,
                'access_type': (
                    'admin'
                    if is_admin
                    else 'member'
                ),
                'domain_count': domains.count(),
            },
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )