from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from rest_framework.views import APIView

from identity.models import  Domain, UserGroup, User_Domain_Tag
from domain_tag_management.serializers.domain_list import (DomainRegisterSerializer, TagListSerializer)

from drf_yasg.utils import swagger_auto_schema

# List of All Domains with Tag Visibility Logic
class DomainDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the list of domains along with allowed tags and the tag-addition availability status",
        responses={
            200: DomainRegisterSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden"
        }
    )
    def get(self, request):
        user = request.user
        role_code = user.role.code if user.role else None

        is_admin = user.is_superuser or (role_code in ['admin', 'super_admin'])
        is_limited = (role_code in ['limited', 'restricted'])

        if is_admin:
            domains = Domain.objects.filter(deleted_at__isnull=True)
        else:
            user_groups = UserGroup.objects.filter(user=user).values_list('group_id', flat=True)
            domains = Domain.objects.filter(
                Q(groups__in=user_groups) | Q(groups__isnull=True),
                deleted_at__isnull=True
            ).distinct()

        result = []
        for domain in domains:
            domain_tags_qs = User_Domain_Tag.objects.filter(domain=domain).select_related('tag', 'user__role')

            main_tags = [
                udt.tag for udt in domain_tags_qs
                if udt.user and udt.user.role and udt.user.role.code in ['admin', 'super_admin']
            ]
            has_main_tag = len(main_tags) > 0

            user_tags = [
                udt.tag for udt in domain_tags_qs
                if udt.user == user
            ]
            has_user_tag = len(user_tags) > 0

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
                unique_tags_dict = {t.id: t for t in (main_tags + user_tags)}
                visible_tags = list(unique_tags_dict.values())

                can_add_tag = not has_user_tag

            domain_data = DomainRegisterSerializer(domain).data
            domain_data['tags'] = TagListSerializer(visible_tags, many=True).data
            domain_data['can_add_tag'] = can_add_tag
            domain_data['has_main_tag'] = has_main_tag

            result.append(domain_data)
        return Response(result, status=status.HTTP_200_OK)