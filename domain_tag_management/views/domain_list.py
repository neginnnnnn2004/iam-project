from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from identity.models import  Domain, UserGroup, User_Domain_Tag
from domain_tag_management.serializers.domain_list import (DomainListSerializer, TagListSerializer)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class DomainListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# List of All Domains with Tag Visibility Logic
class DomainListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = DomainListPagination
    @swagger_auto_schema(
        operation_description="""
        Retrieve the paginated list of domains for the authenticated user,
        with optional search by domain name.
        """,
        manual_parameters=[
            openapi.Parameter(
                'search', openapi.IN_QUERY,
                description="Search by domain name (partial match)",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Items per page (max 100)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: DomainListSerializer(many=True),
            401: "Unauthorized",
        }
    )
    def get(self, request):
        user = request.user
        role_code = user.role.code if user.role else None

        is_admin = user.is_superuser or (role_code in ['admin', 'super_admin'])
        is_limited = (role_code in ['limited'])

        if is_admin:
            domains = Domain.objects.filter(deleted_at__isnull=True)
        else:
            user_groups = UserGroup.objects.filter(user=user).values_list('group_id', flat=True)
            domains = Domain.objects.filter(
                Q(groups__in=user_groups) | Q(groups__isnull=True),
                deleted_at__isnull=True
            ).distinct()

        # ---- Search ----
        search_query = request.query_params.get('search', ' ').strip()
        if search_query:
            domains = domains.filter(domain_name__icontains=search_query)

        domains = domains.order_by('domain_name')

        # ---- Pagination ----
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(domains, request, view=self)

        # ---- Bulk-fetch tags only for the current page ----
        domain_ids = [d.id for d in page]
        all_tags = User_Domain_Tag.objects.filter(
            domain_id__in=domain_ids,
            deleted_at__isnull=True
        ).select_related('tag', 'user__role')

        tags_by_domain = {}
        for udt in all_tags:
            tags_by_domain.setdefault(udt.domain_id, []).append(udt)

        result = []
        for domain in page:
            domain_tags = tags_by_domain.get(domain.id, [])

            main_tags = [
                udt.tag for udt in domain_tags
                if udt.user and udt.user.role and udt.user.role.code in ['admin', 'super_admin']
            ]
            has_main_tag = len(main_tags) > 0

            user_tags = [
                udt.tag for udt in domain_tags
                if udt.user == user
            ]
            has_user_tag = len(user_tags) > 0

            if is_admin:
                visible_tags = [udt.tag for udt in domain_tags]
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

            domain_data = DomainListSerializer(domain).data
            domain_data['tags'] = TagListSerializer(visible_tags, many=True).data
            domain_data['can_add_tag'] = can_add_tag
            domain_data['has_main_tag'] = has_main_tag

            result.append(domain_data)
        return Response(result, status=status.HTTP_200_OK)