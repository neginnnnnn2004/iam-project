from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from identity.models import Domain, Tag, User_Domain_Tag
from identity.permissions import IsAllowedUser
from domain_tag_management.serializers.assign_tag_to_domain import (BulkSyncDomainTagsSerializer)


class BulkSyncDomainTagsView(APIView):
    """
    Handle bulk synchronization of user-domain tags.

    A single request can contain:
        - Add operations
        - Update operations
        - Soft-delete operations

    All operations are validated before any database changes are made.
    If validation fails, no changes are applied.

    When validation succeeds, all database operations are executed
    inside a single atomic transaction.
    """

    permission_classes = [IsAuthenticated, IsAllowedUser]

    def _check_user_access(self, user):
        """
        Check whether the current user is allowed to modify tags.

        Restricted users are not allowed to add, update, or delete tags.
        """
        role_code = user.role.code if user.role else None

        if role_code == 'limited':
            return False, Response(
                {
                    "error_code": 403,
                    "message": {
                        "fa": "کاربران محدودشده امکان افزودن، ویرایش یا حذف تگ را ندارند.",
                        "en": "Restricted users are not allowed to add, edit, or delete tags."
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return True, None

    def _is_admin(self, user):
        """
        Determine whether the user has administrative privileges.
        """
        return user.is_superuser or (
            user.role.code in ['admin', 'super_admin']
            if user.role else False
        )

    def _get_domain_by_name(self, domain_name, index):
        """
        Retrieve an active domain by its domain name.
        """
        if not domain_name:
            return None, {
                "index": index,
                "fa": "نام دامنه ارسال نشده است.",
                "en": "Domain name was not provided."
            }

        try:
            return Domain.objects.get(
                domain_name=domain_name,
                deleted_at__isnull=True
            ), None

        except Domain.DoesNotExist:
            return None, {
                "index": index,
                "domain_name": domain_name,
                "fa": f"دامنه «{domain_name}» یافت نشد.",
                "en": f"Domain «{domain_name}» was not found."
            }

    def _get_tag_by_title(self, title, index):
        """
        Retrieve an active tag by its title.
        """
        if not title:
            return None, {
                "index": index,
                "fa": "عنوان تگ ارسال نشده است.",
                "en": "Tag title was not provided."
            }

        try:
            return Tag.objects.get(
                title=title,
                is_active=True,
                deleted_at__isnull=True
            ), None

        except Tag.DoesNotExist:
            return None, {
                "index": index,
                "title": title,
                "fa": f"تگ «{title}» یافت نشد یا غیرفعال است.",
                "en": f"Tag «{title}» was not found or is inactive."
            }

    def _has_main_tag(self, domain):
        """
        Determine whether the domain has an active main tag.

        A main tag is a User_Domain_Tag assigned by a user whose role
        is admin or super_admin.
        """
        return User_Domain_Tag.objects.filter(
            domain=domain,
            user__role__code__in=['admin', 'super_admin'],
            deleted_at__isnull=True
        ).exists()

    @swagger_auto_schema(
        operation_description="""
        Bulk synchronization of domain tags.

        This endpoint allows adding, updating, and soft-deleting
        multiple user-domain tags in a single request.

        All operations are validated before execution.
        If any operation fails, no changes are applied.

        All successful operations are executed atomically.
        """,
        request_body=BulkSyncDomainTagsSerializer,
        responses={
            200: "Changes were saved successfully.",
            400: "Bad Request",
            403: "Forbidden",
            409: "Conflict - confirmation required"
        }
    )
    def post(self, request):
        """
        Validate and apply add, update, and delete operations.
        """

        # ============================================================
        # 1. Access control
        # ============================================================

        has_access, response = self._check_user_access(
            request.user
        )

        if not has_access:
            return response

        user = request.user
        is_admin = self._is_admin(user)

        # ============================================================
        # 2. Validate request structure
        # ============================================================

        serializer = BulkSyncDomainTagsSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                {
                    "error_code": 60,
                    "message": {
                        "fa": "اطلاعات ارسال شده نامعتبر است.",
                        "en": "The submitted data is invalid."
                    },
                    "detail": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        add_items = data.get("add", [])
        update_items = data.get("update", [])
        delete_items = data.get("delete", [])

        errors = []
        requires_confirmation = []

        items_to_create = []
        items_to_update = []
        ids_to_delete = set()

        # ============================================================
        # Temporary state
        # ============================================================

        user_tags_by_domain = {}
        domains_cache = {}
        tags_cache = {}

        def get_domain(domain_name, index):
            if domain_name in domains_cache:
                return domains_cache[domain_name], None

            domain, error = self._get_domain_by_name(
                domain_name,
                index
            )

            if domain:
                domains_cache[domain_name] = domain

            return domain, error

        def get_tag(title, index):
            if title in tags_cache:
                return tags_cache[title], None

            tag, error = self._get_tag_by_title(
                title,
                index
            )

            if tag:
                tags_cache[title] = tag

            return tag, error

        def get_user_tags(domain):
            """
            Get active tags belonging to the current user for a domain.
            Results are cached to reflect changes made during this request.
            """
            if domain.id not in user_tags_by_domain:
                user_tags_by_domain[domain.id] = list(
                    User_Domain_Tag.objects.filter(
                        user=user,
                        domain=domain,
                        deleted_at__isnull=True
                    ).select_related("tag")
                )

            return user_tags_by_domain[domain.id]

        # ============================================================
        # 3. DELETE validation
        # ============================================================

        for index, item in enumerate(delete_items):

            domain_name = item.get("domain_name")
            title = item.get("title")

            domain, error = get_domain(
                domain_name,
                index
            )

            if error:
                errors.append({
                    "operation": "delete",
                    **error
                })
                continue

            user_existing_udts = get_user_tags(domain)

            if not user_existing_udts:
                errors.append({
                    "operation": "delete",
                    "domain_name": domain.domain_name,
                    "fa": (
                        f"دامنه «{domain.domain_name}»: "
                        "تگ فعالی متعلق به شما برای حذف یافت نشد."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}»: "
                        "no active tag belonging to you was found to delete."
                    )
                })
                continue

            # Delete a specific tag
            if title:
                tag, error = get_tag(
                    title,
                    index
                )

                if error:
                    errors.append({
                        "operation": "delete",
                        **error
                    })
                    continue

                matching_udts = [
                    udt
                    for udt in user_existing_udts
                    if udt.tag_id == tag.id
                ]

                if not matching_udts:
                    errors.append({
                        "operation": "delete",
                        "domain_name": domain.domain_name,
                        "title": title,
                        "fa": (
                            f"دامنه «{domain.domain_name}»: "
                            f"تگ «{title}» توسط شما روی این دامنه ثبت نشده است."
                        ),
                        "en": (
                            f"Domain «{domain.domain_name}»: "
                            f"tag «{title}» has not been registered by you "
                            "on this domain."
                        )
                    })
                    continue

                for udt in matching_udts:
                    ids_to_delete.add(udt.id)

                user_tags_by_domain[domain.id] = [
                    udt
                    for udt in user_existing_udts
                    if udt.tag_id != tag.id
                ]

            # Delete all user's active tags on this domain
            else:
                for udt in user_existing_udts:
                    ids_to_delete.add(udt.id)

                user_tags_by_domain[domain.id] = []

        # ============================================================
        # 4. UPDATE validation
        # ============================================================

        for index, item in enumerate(update_items):

            domain_name = item.get("domain_name")
            old_title = item.get("old_title")
            new_title = item.get("title")
            confirm = item.get("confirm", False)

            domain, error = get_domain(
                domain_name,
                index
            )

            if error:
                errors.append({
                    "operation": "update",
                    **error
                })
                continue

            user_existing_udts = get_user_tags(domain)

            if not user_existing_udts:
                errors.append({
                    "operation": "update",
                    "domain_name": domain.domain_name,
                    "fa": (
                        f"دامنه «{domain.domain_name}»: "
                        "تگی متعلق به شما برای ویرایش وجود ندارد."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}»: "
                        "there is no tag belonging to you to edit."
                    )
                })
                continue

            # Regular users cannot modify their tags if a main tag exists.
            has_main_tag = self._has_main_tag(domain)

            if has_main_tag and not is_admin:
                errors.append({
                    "operation": "update",
                    "domain_name": domain.domain_name,
                    "fa": (
                        f"دامنه «{domain.domain_name}» دارای تگ اصلی است "
                        "و امکان تغییر تگ ندارد."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}» has a primary tag "
                        "and cannot have its tag changed."
                    )
                })
                continue

            # Find old tag
            old_tag, error = get_tag(
                old_title,
                index
            )

            if error:
                errors.append({
                    "operation": "update",
                    **error
                })
                continue

            matching_udts = [
                udt
                for udt in user_existing_udts
                if udt.tag_id == old_tag.id
            ]

            if not matching_udts:
                errors.append({
                    "operation": "update",
                    "domain_name": domain.domain_name,
                    "old_title": old_title,
                    "fa": (
                        f"تگ «{old_title}» برای دامنه "
                        f"«{domain.domain_name}» یافت نشد."
                    ),
                    "en": (
                        f"Tag «{old_title}» was not found for domain "
                        f"«{domain.domain_name}»."
                    )
                })
                continue

            existing_udt = matching_udts[0]

            # Cannot update a tag that is already scheduled for deletion.
            if existing_udt.id in ids_to_delete:
                errors.append({
                    "operation": "update",
                    "domain_name": domain.domain_name,
                    "old_title": old_title,
                    "fa": (
                        "تگی که در همین درخواست برای حذف انتخاب شده "
                        "قابل ویرایش نیست."
                    ),
                    "en": (
                        "A tag scheduled for deletion cannot be updated "
                        "in the same request."
                    )
                })
                continue

            # Find new tag
            new_tag, error = get_tag(
                new_title,
                index
            )

            if error:
                errors.append({
                    "operation": "update",
                    **error
                })
                continue

            # Nothing to change
            if existing_udt.tag_id == new_tag.id:
                errors.append({
                    "operation": "update",
                    "domain_name": domain.domain_name,
                    "old_title": old_title,
                    "title": new_title,
                    "fa": (
                        f"تگ «{new_title}» هم‌اکنون برای این دامنه فعال است "
                        "و تغییری ایجاد نمی‌شود."
                    ),
                    "en": (
                        f"Tag «{new_title}» is already active for this "
                        "domain and no change is required."
                    )
                })
                continue

            # Confirmation required
            if not confirm:
                requires_confirmation.append({
                    "domain_name": domain.domain_name,
                    "old_tag": old_tag.title,
                    "new_tag": new_tag.title
                })
                continue

            existing_udt.tag = new_tag
            existing_udt.updated_at = timezone.now()

            items_to_update.append(existing_udt)

            user_tags_by_domain[domain.id] = [
                existing_udt
                if udt.id == existing_udt.id
                else udt
                for udt in user_existing_udts
            ]

        # ============================================================
        # 5. ADD validation
        # ============================================================

        pending_creations_per_domain = {}

        for index, item in enumerate(add_items):

            domain_name = item.get("domain_name")
            title = item.get("title")

            domain, error = get_domain(
                domain_name,
                index
            )

            if error:
                errors.append({
                    "operation": "add",
                    **error
                })
                continue

            # Regular users cannot add tags to domains
            # that have a main tag.
            has_main_tag = self._has_main_tag(domain)

            if has_main_tag and not is_admin:
                errors.append({
                    "operation": "add",
                    "domain_name": domain.domain_name,
                    "fa": (
                        f"دامنه «{domain.domain_name}» دارای تگ اصلی است "
                        "و امکان افزودن تگ جدید ندارد."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}» has a primary tag "
                        "and cannot have new tags added."
                    )
                })
                continue

            tag, error = get_tag(
                title,
                index
            )

            if error:
                errors.append({
                    "operation": "add",
                    **error
                })
                continue

            user_existing_udts = get_user_tags(domain)

            # Prevent duplicate tag assignment
            if any(
                udt.tag_id == tag.id
                for udt in user_existing_udts
            ):
                errors.append({
                    "operation": "add",
                    "domain_name": domain.domain_name,
                    "title": title,
                    "fa": (
                        f"تگ «{title}» قبلاً توسط شما برای دامنه "
                        f"«{domain.domain_name}» ثبت شده است."
                    ),
                    "en": (
                        f"Tag «{title}» has already been registered by you "
                        f"for domain «{domain.domain_name}»."
                    )
                })
                continue

            pending_count = pending_creations_per_domain.get(
                domain.id,
                0
            )

            effective_tag_count = (
                len(user_existing_udts)
                + pending_count
            )

            max_allowed_tags = 2 if is_admin else 1

            if effective_tag_count >= max_allowed_tags:
                errors.append({
                    "operation": "add",
                    "domain_name": domain.domain_name,
                    "fa": (
                        f"دامنه «{domain.domain_name}»: "
                        f"به سقف مجاز انتخاب تگ ({max_allowed_tags}) رسیده است."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}»: "
                        f"reached the maximum allowed tag limit "
                        f"({max_allowed_tags})."
                    )
                })
                continue

            new_udt = User_Domain_Tag(
                user=user,
                domain=domain,
                tag=tag
            )

            items_to_create.append(new_udt)

            pending_creations_per_domain[domain.id] = (
                pending_count + 1
            )

            # Update temporary state
            user_tags_by_domain[domain.id].append(
                new_udt
            )

        # ============================================================
        # 6. Return validation errors
        # ============================================================

        if errors:
            return Response(
                {
                    "error_code": 60,
                    "message": {
                        "fa": "برخی از تغییرات معتبر نیستند.",
                        "en": "Some changes are invalid."
                    },
                    "detail": errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ============================================================
        # 7. Confirmation check
        # ============================================================

        if requires_confirmation:
            return Response(
                {
                    "error_code": 21,
                    "message": {
                        "fa": "برخی از ویرایش‌ها نیاز به تأیید نهایی دارند.",
                        "en": "Some updates require final confirmation."
                    },
                    "detail": {
                        "requires_confirmation": True,
                        "conflicts": requires_confirmation
                    }
                },
                status=status.HTTP_409_CONFLICT
            )

        # ============================================================
        # 8. Atomic database operation
        # ============================================================

        with transaction.atomic():

            # DELETE
            if ids_to_delete:
                User_Domain_Tag.objects.filter(
                    id__in=ids_to_delete
                ).update(
                    deleted_at=timezone.now()
                )

            # UPDATE
            if items_to_update:
                User_Domain_Tag.objects.bulk_update(
                    items_to_update,
                    fields=[
                        'tag',
                        'updated_at'
                    ]
                )

            # ADD
            if items_to_create:
                User_Domain_Tag.objects.bulk_create(
                    items_to_create
                )

        # ============================================================
        # 9. Success response
        # ============================================================

        return Response(
            {
                "message": {
                    "fa": "تمام تغییرات با موفقیت ذخیره شدند.",
                    "en": "All changes were saved successfully."
                },
                "result": {
                    "added": len(items_to_create),
                    "updated": len(items_to_update),
                    "deleted": len(ids_to_delete)
                }
            },
            status=status.HTTP_200_OK
        )