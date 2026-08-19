from urllib.parse import urlparse

from django.db import transaction
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import status
from rest_framework.views import APIView

from identity.models import  Domain
from identity.permissions import IsAdminRole

from domain_tag_management.serializers.import_update_or_delete_domain import (DomainImportOrEditSerializer, DomainDeleteSerializer)

from drf_yasg.utils import swagger_auto_schema


def extract_root_domain(url_or_domain: str) -> str:
    url_or_domain = url_or_domain.strip().lower()

    if not url_or_domain.startswith(("http://", "https://")):
        url_or_domain = "http://" + url_or_domain

    parsed = urlparse(url_or_domain)
    domain_name = parsed.netloc or parsed.path

    domain_name = domain_name.split(":")[0]

    parts = domain_name.split(".")
    if len(parts) > 2:
        return ".".join(parts[-2:])
    return domain_name

#  import or update(edit) domain by admin (Bulk & Single Enabled)
class ImportOrEditDomainView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="Bulk or single addition of domains with admin access (automatic validation, duplicate removal, and root domain extraction)",
        request_body=DomainImportOrEditSerializer(many=True),
        responses={
            201: DomainImportOrEditSerializer(many=True),
            400: "Bad Request (Code 10)"
        }
    )
    def post(self, request):
        raw_data = request.data
        is_many = isinstance(raw_data, list)
        items = raw_data if is_many else [raw_data]

        existing_domains = set(
            Domain.objects.filter(deleted_at__isnull=True)
            .values_list('domain_name', flat=True)
        )

        seen_in_request = set()
        cleaned_items = []
        skipped_domains = []

        for item in items:
            original_name = item.get('domain_name', '')
            if not original_name:
                continue

            root_domain = extract_root_domain(original_name)

            if root_domain in existing_domains or root_domain in seen_in_request:
                skipped_domains.append(original_name)
                continue

            seen_in_request.add(root_domain)
            item_copy = item.copy()
            item_copy['domain_name'] = root_domain
            cleaned_items.append(item_copy)

        if not cleaned_items:
            return Response({
                "message": {
                    "fa": "تمامی دامنه‌های ارسالی تکراری بوده و از فرآیند ثبت حذف شدند.",
                    "en": "All submitted domains were duplicates and removed from the registration process.",
                },
                "skipped_domains": skipped_domains,
                "created_domains": []
            }, status=status.HTTP_200_OK)

        serializer = DomainImportOrEditSerializer(data=cleaned_items, many=True)

        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": {
                    "fa": "اطلاعات ارسالی برای ایمپورت دامنه معتبر نیست.",
                    "en": "The submitted data for domain import is not valid.",
                },
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        domains_to_create = []

        for  validated_data in serializer.validated_data:
            domain_instance = Domain(
                **validated_data,
                created_by = request.user
            )
            domains_to_create.append(domain_instance)
        with transaction.atomic():
            created_instances = Domain.objects.bulk_create(
                domains_to_create
            )


        created_data = DomainImportOrEditSerializer(created_instances, many=True).data

        response_payload = {
            "message": {
                "fa": "فرآیند ایمپورت با موفقیت انجام شد.",
                "en": "The import process completed successfully.",
            },
            "created_count": len(created_instances),
            "skipped_count": len(skipped_domains),
            "skipped_domains": skipped_domains,
            "created_domains": created_data
        }

        return Response(
            response_payload if is_many else (created_data[0] if created_data else {}),
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="""
        Edit domain information individually or in bulk, with admin access.

        - For single update: Send an Object: {"domain_name": "a.com", "description": "new"}
        - For bulk update: Send an Array: [{"domain_name": "a.com", ...}, ...]
        """,
        request_body=DomainImportOrEditSerializer(many=True),
        responses={
            200: "Domains updated successfully",
            400: "Bad Request (Code 10)"
        }
    )
    def patch(self, request):
        data = request.data

        if isinstance(data, list):
            updated_domains = []
            errors = {}

            with transaction.atomic():
                for index, item in enumerate(data):
                    domain_name = item.get('domain_name')
                    if not domain_name:
                        errors[f"item_{index}"] = {
                            "fa": "ارسال فیلد domain_name برای ویرایش الزامی است.",
                            "en": "The domain_name field is required for editing."
                        }
                        continue

                    try:
                        domain_instance = Domain.objects.get(domain_name=domain_name)
                    except Domain.DoesNotExist:
                        errors[f"item_{index}"] = {
                            "fa": f"دامنه با نام «{domain_name}» یافت نشد.",
                            "en": f"Domain with name «{domain_name}» was not found."
                        }
                        continue

                    serializer = DomainImportOrEditSerializer(domain_instance, data=item, partial=True)
                    if not serializer.is_valid():
                        errors[f"item_{index}"] = serializer.errors
                        continue

                    updated_instance = serializer.save()
                    updated_domains.append(updated_instance)

                if errors:
                    transaction.set_rollback(True)
                    return Response({
                        "error_code": 10,
                        "message": {
                            "fa": "برخی از اطلاعات ارسالی برای ویرایش نامعتبر هستند.",
                            "en": "Some of the submitted data for editing is invalid."
                        },
                        "detail": errors
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "message": {
                    "fa": f"مشخصات تعداد {len(updated_domains)} دامنه با موفقیت بروزرسانی شد.",
                    "en": f"Details of {len(updated_domains)} domain(s) were updated successfully."
                },
                "data": DomainImportOrEditSerializer(updated_domains, many=True).data
            }, status=status.HTTP_200_OK)

        else:
            domain_name = data.get('domain_name')
            if not domain_name:
                return Response({
                    "error_code": 10,
                    "message": {
                        "fa": "ارسال فیلد domain_name در بدنه درخواست الزامی است.",
                        "en": "The domain_name field is required in the request body."
                    },
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                domain = Domain.objects.get(domain_name=domain_name)
            except Domain.DoesNotExist:
                return Response({
                    "error": {
                        "fa": f"دامنه‌ای با نام «{domain_name}» یافت نشد.",
                        "en": f"Domain with name «{domain_name}» was not found."
                    },
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = DomainImportOrEditSerializer(domain, data=data, partial=True)
            if not serializer.is_valid():
                return Response({
                    "error_code": 10,
                    "message": {
                        "fa": "اطلاعات ارسالی معتبر نیست.",
                        "en": "The submitted data is not valid."
                    },
                    "detail": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            updated_domain = serializer.save()
            return Response(DomainImportOrEditSerializer(updated_domain).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""
        Soft delete domain(s) with admin access.

        - For single delete:
          {
              "domain_name": "example.com"
          }

        - For bulk delete:
          [
              {"domain_name": "example.com"},
              {"domain_name": "test.com"}
          ]

        Deleted domains are soft-deleted by setting deleted_at.
        """,
        request_body=DomainDeleteSerializer(many=True),
        responses={
            200: "Domains deleted successfully",
            400: "Bad Request",
            404: "Domain not found"
        }
    )
    def delete(self, request):
        data = request.data

        # Bulk Delete
        if isinstance(data, list):
            deleted_domains = []
            errors = {}

            with transaction.atomic():
                for index, item in enumerate(data):
                    domain_name = item.get('domain_name')
                    if not domain_name:
                        errors[f"item_{index}"] = {
                            "fa": "ارسال فیلد domain_name برای حذف الزامی است.",
                            "en": "The domain_name field is required for deleting."
                        }
                        continue

                    try:
                        domain_instance = Domain.objects.get(
                            domain_name=domain_name,
                            deleted_at__isnull=True
                        )

                    except Domain.DoesNotExist:
                        errors[f"item_{index}"] = {
                            "fa": f"دامنه با نام «{domain_name}» یافت نشد.",
                            "en": f"Domain with name «{domain_name}» was not found."
                        }
                        continue

                    domain_instance.deleted_at = timezone.now()
                    domain_instance.save(
                        update_fields=['deleted_at']
                    )

                    deleted_domains.append(domain_instance)

                if errors:
                    transaction.set_rollback(True)
                    return Response(
                        {
                            "error_code": 10,
                            "message": {
                                "fa": "برخی از دامنه‌ها قابل حذف نیستند.",
                                "en": "Some domains could not be deleted."
                            },
                            "detail": errors
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            return Response(
                {
                    "message": {
                        "fa": f"{len(deleted_domains)} دامنه با موفقیت حذف شدند.",
                        "en": f"{len(deleted_domains)} domain(s) were deleted successfully."
                    },
                    "deleted_count": len(deleted_domains),
                    "deleted_domains": [
                        domain.domain_name
                        for domain in deleted_domains
                    ]
                },
                status=status.HTTP_200_OK
            )

        # Single Delete
        domain_name = data.get('domain_name')

        if not domain_name:
            return Response(
                {
                    "error_code": 10,
                    "message": {
                        "fa": "ارسال فیلد domain_name در بدنه درخواست الزامی است.",
                        "en": "The domain_name field is required in the request body."
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            domain = Domain.objects.get(
                domain_name=domain_name,
                deleted_at__isnull=True
            )

        except Domain.DoesNotExist:
            return Response(
                {
                    "error_code": 10,
                    "message": {
                        "fa": f"دامنه‌ای با نام «{domain_name}» یافت نشد.",
                        "en": f"Domain with name «{domain_name}» was not found."
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        domain.deleted_at = timezone.now()
        domain.save(
            update_fields=['deleted_at']
        )

        return Response(
            {
                "message": {
                    "fa": f"دامنه «{domain_name}» با موفقیت حذف شد.",
                    "en": f"Domain «{domain_name}» was deleted successfully."
                },
                "deleted_domain": domain_name
            },
            status=status.HTTP_200_OK
        )