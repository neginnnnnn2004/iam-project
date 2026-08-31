from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from rest_framework.views import APIView

from identity.models import  Domain, UserGroup, User_Domain_Tag
from identity.services import log_critical_event
from domain_tag_management.serializers.domain_list import (DomainListSerializer, TagListSerializer)

from drf_yasg.utils import swagger_auto_schema

# Domain Detail
class DomainDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific domain.",
        responses={
            200: DomainListSerializer,
            401: "Unauthorized",
            403: "Forbidden",
            404: "Domain not found"
        }
    )
    def get(self, request,pk):
        user = request.user
        role_code = user.role.code if user.role else None

        is_admin = user.is_superuser or (role_code in ['admin', 'super_admin'])
        is_limited = (role_code in ['limited'])

        # 1. Get domain
        try:
            domain = Domain.objects.get(pk=pk, deleted_at__isnull=True)

        except Domain.DoesNotExist:
            log_critical_event(
                action="DOMAIN_DETAIL",
                status_type='failed',
                request=request,
                user_id=request.user.id,
                error_code=50,
                extra={
                    'domain_id': pk,
                }
            )
            return Response(
                {
                    "error_code": 50,
                    "message": {
                        "fa": "دامنه مورد نظر یافت نشد.",
                        "en": "The requested domain was not found."
                    },
                    "detail": None
                },
                status=status.HTTP_404_NOT_FOUND
            )
        # 2. Check domain access
        if not is_admin:

            user_groups = UserGroup.objects.filter(
                user=user
            ).values_list(
                'group_id',
                flat=True
            )

            has_access = Domain.objects.filter(
                pk=pk
            ).filter(
                Q(groups__in=user_groups) |
                Q(groups__isnull=True)
            ).exists()

            if not has_access:
                log_critical_event(
                    action="DOMAIN_DETAIL",
                    status_type='failed',
                    request=request,
                    user_id=request.user.id,
                    error_code=50,
                    extra={
                        'domain_id': pk,
                    }
                )
                return Response(
                    {
                        "error_code": 50,
                        "message": {
                            "fa": "شما به این دامنه دسترسی ندارید.",
                            "en": "You do not have access to this domain."
                        },
                        "detail": None
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        # 3. Get domain tags
        domain_tags_qs = User_Domain_Tag.objects.filter(
            domain=domain,
            deleted_at__isnull=True
        ).select_related(
            'tag' ,
            'user__role'
        )

        # 4. Main tags
        main_tags = [
            udt.tag
            for udt in domain_tags_qs
            if (
                udt.user
                and udt.user.role
                and udt.user.role.code in ['admin', 'super_admin']
            )
        ]
        has_main_tag = len(main_tags) > 0

        # 5. Current user's tags
        user_tags = [
            udt.tag
            for udt in domain_tags_qs
            if udt.user == user
        ]

        has_user_tag = len(user_tags) > 0

        # 6. Determine visible tags and permissions
        if is_admin:

            visible_tags = [
                udt.tag
                for udt in domain_tags_qs
            ]

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

            visible_tags = list(
                unique_tags_dict.values()
            )

            can_add_tag = not has_user_tag

        # 7. Serialize domain

        domain_data = DomainListSerializer(domain).data

        domain_data['tags'] = TagListSerializer(
            visible_tags,
            many=True
        ).data

        domain_data['can_add_tag'] = can_add_tag
        domain_data['has_main_tag'] = has_main_tag
        
        log_critical_event(
            action="DOMAIN_DETAIL",
            status_type='success',
            request=request,
            user_id=request.user.id,
            extra={
                'domain_id': domain.id,
            }
        )
        return Response(
            domain_data,
            status=status.HTTP_200_OK
        )