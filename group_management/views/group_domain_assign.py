from django.db import transaction
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from identity.services import log_critical_event
from identity.permissions import IsAdminRole
from identity.models import Group, Domain

from group_management.serializers.group_domain_assign import GroupDomainAssignSerializer


class GroupDomainAssignView(APIView):
    """
    Bulk assign/unassign domains to/from a group (admin access).

    Since a domain belongs to at most one group, assigning a domain
    that already belongs to another group moves it to this group.

    All operations are validated before any database changes are made.
    If validation fails, no changes are applied.
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_group(self, group_id):
        return Group.objects.filter(pk=group_id, deleted_at__isnull=True).first()

    @swagger_auto_schema(
        operation_description="""
        Bulk assign or unassign domains to/from a group (admin access).

        - `add`: list of domain names to assign to this group.
        - `remove`: list of domain names to unassign from this group.

        All operations are validated before execution.
        If any operation fails, no changes are applied.

        Custom error codes:

        code 65: The requested group does not exist or has been deleted.
        code 60: Some of the submitted changes are invalid.
        """,
        manual_parameters=[
            openapi.Parameter(
                'group_id', openapi.IN_PATH,
                description="(ID) Group",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=GroupDomainAssignSerializer,
        responses={
            200: "Changes were saved successfully.",
            400: "Bad Request (Code 60)",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 65)",
        }
    )
    def post(self, request, group_id):
        group = self.get_group(group_id)
        if not group:
            log_critical_event(
                action="GROUP_DOMAIN_ASSIGN",
                status_type='failed',
                request=request,
                user_id=request.user.id,
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

        serializer = GroupDomainAssignSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error_code": 60,
                "message": {
                    "fa": "اطلاعات ارسال شده نامعتبر است.",
                    "en": "The submitted data is invalid."
                },
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        add_items = data.get("add", [])
        remove_items = data.get("remove", [])

        errors = []
        domains_to_add = []
        domains_to_remove = []

        seen_names = set()

        # ---- Validate ADD ----
        for index, item in enumerate(add_items):
            domain_name = item.get("domain_name")

            if domain_name in seen_names:
                errors.append({
                    "operation": "add",
                    "index": index,
                    "domain_name": domain_name,
                    "fa": f"دامنه «{domain_name}» بیش از یک‌بار در درخواست تکرار شده است.",
                    "en": f"Domain «{domain_name}» is duplicated in the request."
                })
                continue

            domain = Domain.objects.filter(
                domain_name=domain_name,
                deleted_at__isnull=True
            ).first()

            if not domain:
                errors.append({
                    "operation": "add",
                    "index": index,
                    "domain_name": domain_name,
                    "fa": f"دامنه «{domain_name}» یافت نشد.",
                    "en": f"Domain «{domain_name}» was not found."
                })
                continue

            if domain.groups_id == group.id:
                errors.append({
                    "operation": "add",
                    "index": index,
                    "domain_name": domain_name,
                    "fa": f"دامنه «{domain_name}» از قبل عضو این گروه است.",
                    "en": f"Domain «{domain_name}» is already assigned to this group."
                })
                continue

            seen_names.add(domain_name)
            domains_to_add.append(domain)

        # ---- Validate REMOVE ----
        for index, item in enumerate(remove_items):
            domain_name = item.get("domain_name")

            if domain_name in seen_names:
                errors.append({
                    "operation": "remove",
                    "index": index,
                    "domain_name": domain_name,
                    "fa": f"دامنه «{domain_name}» بیش از یک‌بار در درخواست تکرار شده است.",
                    "en": f"Domain «{domain_name}» is duplicated in the request."
                })
                continue

            domain = Domain.objects.filter(
                domain_name=domain_name,
                deleted_at__isnull=True
            ).first()

            if not domain:
                errors.append({
                    "operation": "remove",
                    "index": index,
                    "domain_name": domain_name,
                    "fa": f"دامنه «{domain_name}» یافت نشد.",
                    "en": f"Domain «{domain_name}» was not found."
                })
                continue

            if domain.groups_id != group.id:
                errors.append({
                    "operation": "remove",
                    "index": index,
                    "domain_name": domain_name,
                    "fa": f"دامنه «{domain_name}» عضو این گروه نیست.",
                    "en": f"Domain «{domain_name}» does not belong to this group."
                })
                continue

            seen_names.add(domain_name)
            domains_to_remove.append(domain)

        if errors:
            log_critical_event(
                action="GROUP_DOMAIN_ASSIGN",
                status_type='failed',
                request=request,
                user_id=request.user.id,
                error_code=60,
                extra={'group_id': group.id, 'errors': errors},
            )
            return Response({
                "error_code": 60,
                "message": {
                    "fa": "برخی از تغییرات معتبر نیستند.",
                    "en": "Some changes are invalid."
                },
                "detail": errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # ---- Apply changes atomically ----
        with transaction.atomic():
            for domain in domains_to_add:
                domain.groups = group
                domain.updated_at = timezone.now()

            if domains_to_add:
                Domain.objects.bulk_update(domains_to_add, ['groups', 'updated_at'])

            for domain in domains_to_remove:
                domain.groups = None
                domain.updated_at = timezone.now()

            if domains_to_remove:
                Domain.objects.bulk_update(domains_to_remove, ['groups', 'updated_at'])

        log_critical_event(
            action="GROUP_DOMAIN_ASSIGN",
            status_type='success',
            request=request,
            user_id=request.user.id,
            extra={
                'group_id': group.id,
                'added_count': len(domains_to_add),
                'removed_count': len(domains_to_remove),
            },
        )

        return Response({
            "message": {
                "fa": "تغییرات با موفقیت اعمال شد.",
                "en": "Changes were applied successfully."
            },
            "result": {
                "added": len(domains_to_add),
                "removed": len(domains_to_remove),
            }
        }, status=status.HTTP_200_OK)