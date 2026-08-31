from urllib.parse import urlparse

from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from identity.models import Domain
from identity.permissions import IsAdminRole
from identity.services import log_critical_event

from domain_tag_management.serializers.import_update_or_delete_domain import (
    DomainImportOrEditSerializer,
    DomainDeleteSerializer,
)


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


# ============================================================
# Swagger Schemas
# ============================================================

domain_single_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "domain_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Domain name",
            example="example.com",
        ),
        "description": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Domain description",
            example="Example domain",
        ),
        "group": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Group primary key",
            example=1,
        ),
    },
    required=["domain_name"],
)


domain_bulk_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=domain_single_schema,
)


domain_delete_single_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "domain_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Domain name",
            example="example.com",
        ),
    },
    required=["domain_name"],
)


domain_delete_bulk_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=domain_delete_single_schema,
)


# ============================================================
# Response Schemas
# ============================================================

message_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "fa": openapi.Schema(
            type=openapi.TYPE_STRING,
            example="فرآیند با موفقیت انجام شد.",
        ),
        "en": openapi.Schema(
            type=openapi.TYPE_STRING,
            example="The operation completed successfully.",
        ),
    },
)


domain_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "domain_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            example="example.com",
        ),
        "description": openapi.Schema(
            type=openapi.TYPE_STRING,
            example="Example domain",
        ),
        "created_by": openapi.Schema(
            type=openapi.TYPE_STRING,
            example="admin",
        ),
        "group": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            example=1,
            description="Group primary key",
        ),
    },
)


# POST response
import_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "message": message_schema,

        "created_count": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            example=2,
        ),

        "skipped_count": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            example=1,
        ),

        "skipped_domains": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_STRING
            ),
            example=["www.example.com"],
        ),

        "created_domains": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=domain_response_schema,
        ),
    },
)


# PATCH response
edit_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "message": message_schema,

        "updated_count": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            example=2,
        ),

        "updated_domains": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=domain_response_schema,
        ),
    },
)


# DELETE response
delete_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "message": message_schema,

        "deleted_count": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            example=2,
        ),

        "deleted_domains": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_STRING
            ),
            example=[
                "example.com",
                "test.com",
            ],
        ),
    },
)


# ============================================================
# View
# ============================================================

class ImportOrEditDomainView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminRole,
    ]

    # ========================================================
    # POST
    # ========================================================

    @swagger_auto_schema(
        operation_description="""
        Import one or multiple domains with admin access.

        The endpoint accepts BOTH Single and Bulk requests.

        -------------------------
        Single request
        -------------------------

        {
            "domain_name": "example.com",
            "description": "Example domain",
            "group": 1
        }

        -------------------------
        Bulk request
        -------------------------

        [
            {
                "domain_name": "example.com",
                "description": "Example domain",
                "group": 1
            },
            {
                "domain_name": "test.com",
                "description": "Test domain",
                "group": 2
            }
        ]

        Duplicate domains are automatically skipped.

        URLs such as:
            https://www.example.com
            http://example.com
            www.example.com

        are normalized to:
            example.com
        """,

        # Swagger 2.0 limitation:
        # one request body schema cannot represent both
        # object and array simultaneously.
        request_body=domain_single_schema,

        responses={
            201: openapi.Response(
                description=(
                    "Import completed successfully. "
                    "The response structure is the same for "
                    "single and bulk requests."
                ),
                schema=import_response_schema,
            ),

            400: openapi.Response(
                description="Bad Request (Code 10)"
            ),
        },
    )
    def post(self, request):

        raw_data = request.data

        is_many = isinstance(raw_data, list)

        items = raw_data if is_many else [raw_data]

        existing_domains = set(
            Domain.objects
            .filter(deleted_at__isnull=True)
            .values_list(
                "domain_name",
                flat=True,
            )
        )

        seen_in_request = set()

        cleaned_items = []

        skipped_domains = []

        # ----------------------------------------------------
        # Normalize + remove duplicates
        # ----------------------------------------------------

        for item in items:

            original_name = item.get(
                "domain_name",
                "",
            )

            if not original_name:
                continue

            root_domain = extract_root_domain(
                original_name
            )

            if (
                root_domain in existing_domains
                or root_domain in seen_in_request
            ):
                skipped_domains.append(
                    original_name
                )
                continue

            seen_in_request.add(
                root_domain
            )

            item_copy = item.copy()

            item_copy["domain_name"] = root_domain

            cleaned_items.append(
                item_copy
            )

        # ----------------------------------------------------
        # All domains were duplicates
        # ----------------------------------------------------

        if not cleaned_items:

            log_critical_event(
                action="IMPORT_DOMAIN",
                status_type="success",
                request=request,
                user_id=request.user.id,
                extra={
                    "created_count": 0,
                    "skipped_count": len(
                        skipped_domains
                    ),
                    "skipped_domains": skipped_domains,
                },
            )

            return Response(
                {
                    "message": {
                        "fa": (
                            "تمامی دامنه‌های ارسالی "
                            "تکراری بوده و از فرآیند "
                            "ثبت حذف شدند."
                        ),
                        "en": (
                            "All submitted domains were "
                            "duplicates and removed from "
                            "the registration process."
                        ),
                    },

                    "created_count": 0,

                    "skipped_count": len(
                        skipped_domains
                    ),

                    "skipped_domains": skipped_domains,

                    "created_domains": [],
                },

                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        serializer = DomainImportOrEditSerializer(
            data=cleaned_items,
            many=True,
        )

        if not serializer.is_valid():

            log_critical_event(
                action="IMPORT_DOMAIN",
                status_type="failed",
                request=request,
                user_id=request.user.id,
                error_code=10,
                extra={
                    "submitted_domains": [
                        item.get("domain_name")
                        for item in cleaned_items
                    ],
                    "validation_errors": (
                        serializer.errors
                    ),
                },
            )

            return Response(
                {
                    "error_code": 10,

                    "message": {
                        "fa": (
                            "اطلاعات ارسالی برای "
                            "ایمپورت دامنه معتبر نیست."
                        ),
                        "en": (
                            "The submitted data for "
                            "domain import is not valid."
                        ),
                    },

                    "detail": serializer.errors,
                },

                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Prepare instances
        # ----------------------------------------------------

        domains_to_create = []

        for validated_data in serializer.validated_data:

            domain_instance = Domain(
                **validated_data,
                created_by=request.user,
            )

            domains_to_create.append(
                domain_instance
            )

        # ----------------------------------------------------
        # Bulk create
        # ----------------------------------------------------

        with transaction.atomic():

            created_instances = Domain.objects.bulk_create(
                domains_to_create
            )

        created_data = DomainImportOrEditSerializer(
            created_instances,
            many=True,
        ).data

        # ----------------------------------------------------
        # Unified response
        # ----------------------------------------------------

        response_payload = {

            "message": {
                "fa": (
                    "فرآیند ایمپورت "
                    "با موفقیت انجام شد."
                ),
                "en": (
                    "The import process "
                    "completed successfully."
                ),
            },

            "created_count": len(
                created_instances
            ),

            "skipped_count": len(
                skipped_domains
            ),

            "skipped_domains": skipped_domains,

            "created_domains": created_data,
        }

        # ----------------------------------------------------
        # Log
        # ----------------------------------------------------

        log_critical_event(
            action="IMPORT_DOMAIN",
            status_type="success",
            request=request,
            user_id=request.user.id,
            extra={
                "created_count": len(
                    created_instances
                ),

                "skipped_count": len(
                    skipped_domains
                ),

                "created_domains": [
                    domain.domain_name
                    for domain in created_instances
                ],

                "skipped_domains": skipped_domains,
            },
        )

        # مهم:
        # دیگر بر اساس Single/Bulk response متفاوت نیست.
        return Response(
            response_payload,
            status=status.HTTP_201_CREATED,
        )

    # ========================================================
    # PATCH
    # ========================================================

    @swagger_auto_schema(
        operation_description="""
        Edit one or multiple domains.

        The endpoint accepts BOTH Single and Bulk requests.

        -------------------------
        Single request
        -------------------------

        {
            "domain_name": "example.com",
            "description": "New description",
            "group": 1
        }

        -------------------------
        Bulk request
        -------------------------

        [
            {
                "domain_name": "example.com",
                "description": "New description",
                "group": 1
            },
            {
                "domain_name": "test.com",
                "description": "Another description",
                "group": 2
            }
        ]
        """,

        request_body=domain_single_schema,

        responses={
            200: openapi.Response(
                description=(
                    "Domains updated successfully."
                ),
                schema=edit_response_schema,
            ),

            400: openapi.Response(
                description="Bad Request (Code 10)"
            ),

            404: openapi.Response(
                description="Domain not found"
            ),
        },
    )
    def patch(self, request):

        data = request.data

        is_many = isinstance(
            data,
            list,
        )

        items = data if is_many else [data]

        updated_domains = []

        errors = {}

        # ----------------------------------------------------
        # Transaction
        # ----------------------------------------------------

        with transaction.atomic():

            for index, item in enumerate(items):

                domain_name = item.get(
                    "domain_name"
                )

                # --------------------------------------------
                # domain_name required
                # --------------------------------------------

                if not domain_name:

                    errors[f"item_{index}"] = {
                        "fa": (
                            "ارسال فیلد domain_name "
                            "برای ویرایش الزامی است."
                        ),
                        "en": (
                            "The domain_name field "
                            "is required for editing."
                        ),
                    }

                    continue

                # --------------------------------------------
                # Find domain
                # --------------------------------------------

                try:

                    domain_instance = Domain.objects.get(
                        domain_name=domain_name,
                        deleted_at__isnull=True,
                    )

                except Domain.DoesNotExist:

                    errors[f"item_{index}"] = {
                        "fa": (
                            f"دامنه با نام «{domain_name}» "
                            "یافت نشد."
                        ),
                        "en": (
                            f"Domain with name "
                            f"«{domain_name}» was not found."
                        ),
                    }

                    continue

                # --------------------------------------------
                # Validate
                # --------------------------------------------

                serializer = DomainImportOrEditSerializer(
                    domain_instance,
                    data=item,
                    partial=True,
                )

                if not serializer.is_valid():

                    errors[f"item_{index}"] = (
                        serializer.errors
                    )

                    continue

                # --------------------------------------------
                # Save
                # --------------------------------------------

                updated_instance = serializer.save()

                updated_domains.append(
                    updated_instance
                )

            # ------------------------------------------------
            # Any error => rollback everything
            # ------------------------------------------------

            if errors:

                log_critical_event(
                    action="EDIT_DOMAIN",
                    status_type="failed",
                    request=request,
                    user_id=request.user.id,
                    error_code=10,
                    extra={
                        "errors": errors,
                    },
                )

                transaction.set_rollback(
                    True
                )

                return Response(
                    {
                        "error_code": 10,

                        "message": {
                            "fa": (
                                "برخی از اطلاعات ارسالی "
                                "برای ویرایش نامعتبر هستند."
                            ),
                            "en": (
                                "Some of the submitted "
                                "data for editing is invalid."
                            ),
                        },

                        "detail": errors,
                    },

                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ----------------------------------------------------
        # Serialize updated domains
        # ----------------------------------------------------

        updated_data = DomainImportOrEditSerializer(
            updated_domains,
            many=True,
        ).data

        # ----------------------------------------------------
        # Log success
        # ----------------------------------------------------

        log_critical_event(
            action="EDIT_DOMAIN",
            status_type="success",
            request=request,
            user_id=request.user.id,
            extra={
                "domain_count": len(
                    updated_domains
                ),

                "updated_domains": [
                    domain.domain_name
                    for domain in updated_domains
                ],
            },
        )

        # ----------------------------------------------------
        # Unified response
        # ----------------------------------------------------

        return Response(
            {
                "message": {
                    "fa": (
                        f"مشخصات تعداد "
                        f"{len(updated_domains)} دامنه "
                        "با موفقیت بروزرسانی شد."
                    ),
                    "en": (
                        f"Details of "
                        f"{len(updated_domains)} domain(s) "
                        "were updated successfully."
                    ),
                },

                "updated_count": len(
                    updated_domains
                ),

                "updated_domains": updated_data,
            },

            status=status.HTTP_200_OK,
        )

    # ========================================================
    # DELETE
    # ========================================================

    @swagger_auto_schema(
        operation_description="""
        Soft delete one or multiple domains.

        The endpoint accepts BOTH Single and Bulk requests.

        -------------------------
        Single request
        -------------------------

        {
            "domain_name": "example.com"
        }

        -------------------------
        Bulk request
        -------------------------

        [
            {
                "domain_name": "example.com"
            },
            {
                "domain_name": "test.com"
            }
        ]

        Deleted domains are soft-deleted by setting
        the deleted_at field.
        """,

        request_body=domain_delete_single_schema,

        responses={
            200: openapi.Response(
                description=(
                    "Domains deleted successfully."
                ),
                schema=delete_response_schema,
            ),

            400: openapi.Response(
                description="Bad Request (Code 10)"
            ),

            404: openapi.Response(
                description="Domain not found"
            ),
        },
    )
    def delete(self, request):

        data = request.data

        is_many = isinstance(
            data,
            list,
        )

        items = data if is_many else [data]

        deleted_domains = []

        errors = {}

        # ----------------------------------------------------
        # Transaction
        # ----------------------------------------------------

        with transaction.atomic():

            for index, item in enumerate(items):

                # --------------------------------------------
                # Validate using DomainDeleteSerializer
                # --------------------------------------------

                serializer = DomainDeleteSerializer(
                    data=item
                )

                if not serializer.is_valid():

                    errors[f"item_{index}"] = (
                        serializer.errors
                    )

                    continue

                domain_name = (
                    serializer.validated_data[
                        "domain_name"
                    ]
                )

                # --------------------------------------------
                # Find active domain
                # --------------------------------------------

                try:

                    domain_instance = Domain.objects.get(
                        domain_name=domain_name,
                        deleted_at__isnull=True,
                    )

                except Domain.DoesNotExist:

                    errors[f"item_{index}"] = {
                        "fa": (
                            f"دامنه با نام «{domain_name}» "
                            "یافت نشد."
                        ),
                        "en": (
                            f"Domain with name "
                            f"«{domain_name}» was not found."
                        ),
                    }

                    continue

                # --------------------------------------------
                # Soft delete
                # --------------------------------------------

                domain_instance.deleted_at = timezone.now()

                domain_instance.save(
                    update_fields=[
                        "deleted_at"
                    ]
                )

                deleted_domains.append(
                    domain_instance
                )

            # ------------------------------------------------
            # Any error => rollback everything
            # ------------------------------------------------

            if errors:

                log_critical_event(
                    action="DELETE_DOMAIN",
                    status_type="failed",
                    request=request,
                    user_id=request.user.id,
                    error_code=10,
                    extra={
                        "deleted_domains": [
                            domain.domain_name
                            for domain in deleted_domains
                        ],
                        "detail": errors,
                    },
                )

                transaction.set_rollback(
                    True
                )

                return Response(
                    {
                        "error_code": 10,

                        "message": {
                            "fa": (
                                "برخی از دامنه‌ها "
                                "قابل حذف نیستند."
                            ),
                            "en": (
                                "Some domains "
                                "could not be deleted."
                            ),
                        },

                        "detail": errors,
                    },

                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ----------------------------------------------------
        # Log success
        # ----------------------------------------------------

        log_critical_event(
            action="DELETE_DOMAIN",
            status_type="success",
            request=request,
            user_id=request.user.id,
            extra={
                "deleted_count": len(
                    deleted_domains
                ),

                "deleted_domains": [
                    domain.domain_name
                    for domain in deleted_domains
                ],
            },
        )

        # ----------------------------------------------------
        # Unified response
        # ----------------------------------------------------

        return Response(
            {
                "message": {
                    "fa": (
                        f"{len(deleted_domains)} دامنه "
                        "با موفقیت حذف شدند."
                    ),
                    "en": (
                        f"{len(deleted_domains)} domain(s) "
                        "were deleted successfully."
                    ),
                },

                "deleted_count": len(
                    deleted_domains
                ),

                "deleted_domains": [
                    domain.domain_name
                    for domain in deleted_domains
                ],
            },

            status=status.HTTP_200_OK,
        )