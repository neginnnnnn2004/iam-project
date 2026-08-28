from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from identity.models import Domain, Tag, User_Domain_Tag
from identity.permissions import IsAllowedUser
from identity.services import log_critical_event
from domain_tag_management.serializers.assign_tag_to_domain import (BulkSyncDomainTagsSerializer,)


class BulkSyncDomainTagsView(APIView):
    """
    Bulk synchronization of domain tags.

    Business rules:

    1. Admin / Super Admin:
       - Can create main tags.
       - Each domain can have at most 2 main tags in total.
       - The limit of 2 is shared between all admins.
       - Each admin can CRUD only the tags created by themselves.

    2. Regular users:
       - Can have at most one tag per domain.
       - Cannot add, update, or delete tags when the domain has a
         main tag.
       - Can CRUD their own tag while no main tag exists.

    3. Limited users:
       - Access is controlled by _check_user_access().
       - If allowed by that method, they follow the same domain/tag rules
         as regular users.

    4. Delete:
       - Soft delete is used.
       - Deleting a main tag frees one of the two main-tag slots.
       - Regular users cannot delete their tag while a main tag
         exists on the domain. Admins may still delete their own
         main tag.

    5. Update:
       - Updating a main tag does not create another main tag.
       - Ownership remains with the original admin.
    """

    permission_classes = [IsAuthenticated, IsAllowedUser]

    MAX_MAIN_TAGS_PER_DOMAIN = 2
    MAX_NORMAL_TAGS_PER_USER = 1

    # ================================================================
    # Permission helpers
    # ================================================================

    def _check_user_access(self, user):
        """
        Check whether the current user is allowed to modify tags.

        IMPORTANT:
        If limited users are supposed to be allowed to work with tags
        when no main tag exists, remove the hard restriction below.
        """

        role_code = user.role.code if user.role else None

        if role_code == "limited":
            return False, Response(
                {
                    "error_code": 403,
                    "message": {
                        "fa": (
                            "کاربران محدودشده امکان افزودن، "
                            "ویرایش یا حذف تگ را ندارند."
                        ),
                        "en": (
                            "Restricted users are not allowed to "
                            "add, edit, or delete tags."
                        ),
                    },
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return True, None

    def _is_admin(self, user):
        """
        Return True for admin and super_admin users.
        """

        return user.is_superuser or (
            user.role.code in ["admin", "super_admin"]
            if user.role
            else False
        )

    # ================================================================
    # Object helpers
    # ================================================================

    def _get_domain_by_name(self, domain_name, index):
        """
        Retrieve an active domain.
        """

        if not domain_name:
            return None, {
                "index": index,
                "fa": "نام دامنه ارسال نشده است.",
                "en": "Domain name was not provided.",
            }

        try:
            return Domain.objects.get(
                domain_name=domain_name,
                deleted_at__isnull=True,
            ), None

        except Domain.DoesNotExist:
            return None, {
                "index": index,
                "domain_name": domain_name,
                "fa": f"دامنه «{domain_name}» یافت نشد.",
                "en": f"Domain «{domain_name}» was not found.",
            }

    def _get_tag_by_title(self, title, index):
        """
        Retrieve an active tag.
        """

        if not title:
            return None, {
                "index": index,
                "fa": "عنوان تگ ارسال نشده است.",
                "en": "Tag title was not provided.",
            }

        try:
            return Tag.objects.get(
                title=title,
                is_active=True,
                deleted_at__isnull=True,
            ), None

        except Tag.DoesNotExist:
            return None, {
                "index": index,
                "title": title,
                "fa": (
                    f"تگ «{title}» یافت نشد یا غیرفعال است."
                ),
                "en": (
                    f"Tag «{title}» was not found or is inactive."
                ),
            }

    # ================================================================
    # Main tag helpers
    # ================================================================

    def _get_main_tags(self, domain):
        """
        Return active main tags of a domain.

        Main tag:
            A User_Domain_Tag created by admin/super_admin.
        """

        return User_Domain_Tag.objects.filter(
            domain=domain,
            user__role__code__in=["admin", "super_admin"],
            deleted_at__isnull=True,
        ).select_related(
            "user",
            "tag",
        ).order_by(
            "created_at",
            "id",
        )

    def _get_main_tag_count(self, domain):
        """
        Return number of active main tags on a domain.
        """

        return User_Domain_Tag.objects.filter(
            domain=domain,
            user__role__code__in=["admin", "super_admin"],
            deleted_at__isnull=True,
        ).count()

    def _has_main_tag(self, domain):
        """
        Return True if the domain has at least one active main tag.
        """

        return self._get_main_tag_count(domain) > 0

    def _is_main_tag(self, udt):
        """
        Determine whether a User_Domain_Tag is a main tag.
        """

        role_code = (
            udt.user.role.code
            if udt.user and udt.user.role
            else None
        )

        return role_code in ["admin", "super_admin"]

    # ================================================================
    # User tag helper
    # ================================================================

    def _get_user_tags(self, user, domain):
        """
        Return active tags belonging to the current user.
        """

        return list(
            User_Domain_Tag.objects.filter(
                user=user,
                domain=domain,
                deleted_at__isnull=True,
            ).select_related(
                "tag",
                "user",
            )
        )

    # ================================================================
    # Swagger
    # ================================================================

    @swagger_auto_schema(
        operation_description="""
        Bulk synchronization of domain tags.

        ADD:
        - Admin/Super Admin can add main tags.
        - Maximum 2 main tags are allowed per domain.
        - The 2-tag limit is shared between all admins.
        - Regular users can have at most one tag per domain.
        - Regular users cannot add a tag when a main tag exists.

        UPDATE:
        - Users can update only their own tags.
        - Regular users cannot update their tag when a main tag exists.
        - Admins can update their own main tags.

        DELETE:
        - Users can delete only their own tags.
        - Regular users cannot delete their tag when a main tag exists.
        - Admins can delete their own main tags.
        - Deleting a main tag frees one main-tag slot.

        All database modifications are executed atomically.
        """,
        request_body=BulkSyncDomainTagsSerializer,
        responses={
            200: "Changes were saved successfully.",
            400: "Bad Request",
            403: "Forbidden",
            409: "Conflict - confirmation required",
        },
    )
    def post(self, request):
        """
        Validate and execute add, update and delete operations.
        """

        # ============================================================
        # 1. ACCESS CONTROL
        # ============================================================

        has_access, response = self._check_user_access(
            request.user
        )

        if not has_access:
            log_critical_event(
                action="BULK_SYNC_DOMAIN_TAGS",
                status_type="failed",
                request=request,
                user_id=request.user.id,
                error_code=403,
            )
            return response

        user = request.user
        is_admin = self._is_admin(user)

        # ============================================================
        # 2. SERIALIZER VALIDATION
        # ============================================================

        serializer = BulkSyncDomainTagsSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            log_critical_event(
                action="BULK_SYNC_DOMAIN_TAGS",
                status_type="failed",
                request=request,
                user_id=user.id,
                error_code=60,
                extra={"detail": serializer.errors},
            )
            return Response(
                {
                    "error_code": 60,
                    "message": {
                        "fa": "اطلاعات ارسال شده نامعتبر است.",
                        "en": "The submitted data is invalid.",
                    },
                    "detail": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
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

        # Number of NEW main tags that are going to be created
        # during this request.
        pending_main_tags_per_domain = {}

        # ============================================================
        # Local helper functions
        # ============================================================

        def get_domain(domain_name, index):
            if domain_name in domains_cache:
                return domains_cache[domain_name], None

            domain, error = self._get_domain_by_name(
                domain_name,
                index,
            )

            if domain:
                domains_cache[domain_name] = domain

            return domain, error

        def get_tag(title, index):
            if title in tags_cache:
                return tags_cache[title], None

            tag, error = self._get_tag_by_title(
                title,
                index,
            )

            if tag:
                tags_cache[title] = tag

            return tag, error

        def get_user_tags(domain):
            """
            Cached user tags.

            This cache is updated whenever ADD/DELETE/UPDATE changes
            the temporary state during the current request.
            """

            if domain.id not in user_tags_by_domain:
                user_tags_by_domain[domain.id] = (
                    self._get_user_tags(user, domain)
                )

            return user_tags_by_domain[domain.id]

        # ============================================================
        # 3. DELETE VALIDATION
        # ============================================================

        for index, item in enumerate(delete_items):

            domain_name = item.get("domain_name")
            title = item.get("title")

            domain, error = get_domain(
                domain_name,
                index,
            )

            if error:
                errors.append({
                    "operation": "delete",
                    **error,
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
                        "no active tag belonging to you "
                        "was found to delete."
                    ),
                })
                continue

            # --------------------------------------------------------
            # Main tag rule
            #
            # Regular users cannot delete their tag while a main
            # tag exists on the domain. Admins may still delete
            # their own main tag.
            # --------------------------------------------------------

            if self._has_main_tag(domain) and not is_admin:
                errors.append({
                    "operation": "delete",
                    "domain_name": domain.domain_name,
                    "fa": (
                        f"دامنه «{domain.domain_name}» دارای "
                        "تگ اصلی است و امکان حذف تگ "
                        "برای کاربر عادی وجود ندارد."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}» has a "
                        "main tag and regular users cannot "
                        "delete their tag."
                    ),
                })
                continue

            # --------------------------------------------------------
            # Delete specific tag
            # --------------------------------------------------------

            if title:

                tag, error = get_tag(
                    title,
                    index,
                )

                if error:
                    errors.append({
                        "operation": "delete",
                        **error,
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
                            f"تگ «{title}» توسط شما ثبت نشده است."
                        ),
                        "en": (
                            f"Domain «{domain.domain_name}»: "
                            f"tag «{title}» has not been "
                            "registered by you."
                        ),
                    })
                    continue

                for udt in matching_udts:
                    ids_to_delete.add(udt.id)

                user_tags_by_domain[domain.id] = [
                    udt
                    for udt in user_existing_udts
                    if udt.tag_id != tag.id
                ]

            # --------------------------------------------------------
            # Delete all user's tags
            # --------------------------------------------------------

            else:

                for udt in user_existing_udts:
                    ids_to_delete.add(udt.id)

                user_tags_by_domain[domain.id] = []

        # ============================================================
        # 4. UPDATE VALIDATION
        # ============================================================

        for index, item in enumerate(update_items):

            domain_name = item.get("domain_name")
            old_title = item.get("old_title")
            new_title = item.get("title")
            confirm = item.get("confirm", False)

            domain, error = get_domain(
                domain_name,
                index,
            )

            if error:
                errors.append({
                    "operation": "update",
                    **error,
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
                    ),
                })
                continue

            # --------------------------------------------------------
            # Find old tag
            # --------------------------------------------------------

            old_tag, error = get_tag(
                old_title,
                index,
            )

            if error:
                errors.append({
                    "operation": "update",
                    **error,
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
                    ),
                })
                continue

            existing_udt = matching_udts[0]

            # --------------------------------------------------------
            # Cannot update a tag scheduled for deletion
            # --------------------------------------------------------

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
                        "A tag scheduled for deletion cannot be "
                        "updated in the same request."
                    ),
                })
                continue

            # --------------------------------------------------------
            # Main tag rule
            #
            # If current user's tag is a normal tag and a main tag
            # exists, regular user cannot modify it.
            #
            # Admin can modify his/her own main tag.
            # --------------------------------------------------------

            existing_is_main = self._is_main_tag(
                existing_udt
            )

            has_main_tag = self._has_main_tag(domain)

            if has_main_tag and not is_admin:
                errors.append({
                    "operation": "update",
                    "domain_name": domain.domain_name,
                    "fa": (
                        f"دامنه «{domain.domain_name}» دارای "
                        "تگ اصلی است و امکان تغییر تگ "
                        "برای کاربر عادی وجود ندارد."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}» has a "
                        "main tag and regular users cannot "
                        "modify their tag."
                    ),
                })
                continue

            # --------------------------------------------------------
            # Find new tag
            # --------------------------------------------------------

            new_tag, error = get_tag(
                new_title,
                index,
            )

            if error:
                errors.append({
                    "operation": "update",
                    **error,
                })
                continue

            # --------------------------------------------------------
            # Nothing changed
            # --------------------------------------------------------

            if existing_udt.tag_id == new_tag.id:
                errors.append({
                    "operation": "update",
                    "domain_name": domain.domain_name,
                    "old_title": old_title,
                    "title": new_title,
                    "fa": (
                        f"تگ «{new_title}» هم‌اکنون برای این "
                        "دامنه فعال است."
                    ),
                    "en": (
                        f"Tag «{new_title}» is already active "
                        "for this domain."
                    ),
                })
                continue

            # --------------------------------------------------------
            # Confirmation
            # --------------------------------------------------------

            if not confirm:
                requires_confirmation.append({
                    "domain_name": domain.domain_name,
                    "old_tag": old_tag.title,
                    "new_tag": new_tag.title,
                })
                continue

            # --------------------------------------------------------
            # Update
            # --------------------------------------------------------

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
        # 5. ADD VALIDATION
        # ============================================================

        pending_normal_tags_per_domain = {}

        for index, item in enumerate(add_items):

            domain_name = item.get("domain_name")
            title = item.get("title")

            domain, error = get_domain(
                domain_name,
                index,
            )

            if error:
                errors.append({
                    "operation": "add",
                    **error,
                })
                continue

            # --------------------------------------------------------
            # Get tag
            # --------------------------------------------------------

            tag, error = get_tag(
                title,
                index,
            )

            if error:
                errors.append({
                    "operation": "add",
                    **error,
                })
                continue

            user_existing_udts = get_user_tags(domain)

            # --------------------------------------------------------
            # Prevent duplicate assignment by current user
            # --------------------------------------------------------

            if any(
                udt.tag_id == tag.id
                for udt in user_existing_udts
            ):
                errors.append({
                    "operation": "add",
                    "domain_name": domain.domain_name,
                    "title": title,
                    "fa": (
                        f"تگ «{title}» قبلاً توسط شما "
                        f"برای دامنه «{domain.domain_name}» ثبت شده است."
                    ),
                    "en": (
                        f"Tag «{title}» has already been registered "
                        f"by you for domain «{domain.domain_name}»."
                    ),
                })
                continue

            # ========================================================
            # ADMIN ADD
            # ========================================================

            if is_admin:

                current_main_tag_count = (
                    self._get_main_tag_count(domain)
                )

                pending_main_count = (
                    pending_main_tags_per_domain.get(
                        domain.id,
                        0,
                    )
                )

                effective_main_tag_count = (
                    current_main_tag_count
                    + pending_main_count
                )

                # ----------------------------------------------------
                # MAX 2 MAIN TAGS PER DOMAIN
                # ----------------------------------------------------

                if (
                    effective_main_tag_count
                    >= self.MAX_MAIN_TAGS_PER_DOMAIN
                ):
                    errors.append({
                        "operation": "add",
                        "domain_name": domain.domain_name,
                        "title": title,
                        "fa": (
                            f"دامنه «{domain.domain_name}» "
                            "قبلاً به سقف ۲ تگ اصلی رسیده است. "
                            "امکان افزودن تگ اصلی جدید وجود ندارد."
                        ),
                        "en": (
                            f"Domain «{domain.domain_name}» has "
                            "already reached the maximum of "
                            "2 main tags. No additional main tag "
                            "can be added."
                        ),
                    })
                    continue

                # ----------------------------------------------------
                # Create MAIN TAG
                # ----------------------------------------------------

                new_udt = User_Domain_Tag(
                    user=user,
                    domain=domain,
                    tag=tag,
                )

                items_to_create.append(new_udt)

                pending_main_tags_per_domain[
                    domain.id
                ] = pending_main_count + 1

                user_tags_by_domain[
                    domain.id
                ].append(new_udt)

                continue

            # ========================================================
            # REGULAR USER ADD
            # ========================================================

            has_main_tag = self._has_main_tag(domain)

            if has_main_tag:
                errors.append({
                    "operation": "add",
                    "domain_name": domain.domain_name,
                    "title": title,
                    "fa": (
                        f"دامنه «{domain.domain_name}» دارای "
                        "تگ اصلی است و امکان افزودن تگ جدید "
                        "برای کاربر عادی وجود ندارد."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}» has "
                        "a main tag and regular users cannot "
                        "add a new tag."
                    ),
                })
                continue

            # --------------------------------------------------------
            # Regular user: maximum 1 tag
            # --------------------------------------------------------

            pending_normal_count = (
                pending_normal_tags_per_domain.get(
                    domain.id,
                    0,
                )
            )

            effective_normal_tag_count = (
                len(user_existing_udts)
                + pending_normal_count
            )

            if (
                effective_normal_tag_count
                >= self.MAX_NORMAL_TAGS_PER_USER
            ):
                errors.append({
                    "operation": "add",
                    "domain_name": domain.domain_name,
                    "title": title,
                    "fa": (
                        f"دامنه «{domain.domain_name}»: "
                        "شما قبلاً یک تگ برای این دامنه ثبت کرده‌اید."
                    ),
                    "en": (
                        f"Domain «{domain.domain_name}»: "
                        "you already have one tag for this domain."
                    ),
                })
                continue

            # --------------------------------------------------------
            # Create NORMAL TAG
            # --------------------------------------------------------

            new_udt = User_Domain_Tag(
                user=user,
                domain=domain,
                tag=tag,
            )

            items_to_create.append(new_udt)

            pending_normal_tags_per_domain[
                domain.id
            ] = pending_normal_count + 1

            user_tags_by_domain[
                domain.id
            ].append(new_udt)

        # ============================================================
        # 6. VALIDATION ERRORS
        # ============================================================

        if errors:
            log_critical_event(
                action="BULK_SYNC_DOMAIN_TAGS",
                status_type="failed",
                request=request,
                user_id=user.id,
                error_code=60,
                extra={"detail": errors},
            )
            return Response(
                {
                    "error_code": 60,
                    "message": {
                        "fa": "برخی از تغییرات معتبر نیستند.",
                        "en": "Some changes are invalid.",
                    },
                    "detail": errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ============================================================
        # 7. CONFIRMATION
        # ============================================================

        if requires_confirmation:
            log_critical_event(
                action="BULK_SYNC_DOMAIN_TAGS",
                status_type="pending",
                request=request,
                user_id=user.id,
                error_code=21,
                extra={"conflicts": requires_confirmation},
            )
            return Response(
                {
                    "error_code": 21,
                    "message": {
                        "fa": (
                            "برخی از ویرایش‌ها نیاز به "
                            "تأیید نهایی دارند."
                        ),
                        "en": (
                            "Some updates require final confirmation."
                        ),
                    },
                    "detail": {
                        "requires_confirmation": True,
                        "conflicts": requires_confirmation,
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

        # ============================================================
        # 8. ATOMIC DATABASE OPERATION
        # ============================================================

        with transaction.atomic():

            # --------------------------------------------------------
            # Lock domains involved in main-tag creation.
            #
            # This prevents two admins from simultaneously passing
            # the "max 2 main tags" validation.
            # --------------------------------------------------------

            admin_add_domains = {
                item.get("domain_name")
                for item in add_items
            }

            if is_admin and admin_add_domains:

                locked_domains = list(
                    Domain.objects.select_for_update().filter(
                        domain_name__in=admin_add_domains,
                        deleted_at__isnull=True,
                    )
                )

                locked_domains_by_name = {
                    domain.domain_name: domain
                    for domain in locked_domains
                }

                # Re-check main-tag limit after obtaining the lock.
                for domain_name in admin_add_domains:

                    domain = locked_domains_by_name.get(
                        domain_name
                    )

                    if not domain:
                        continue

                    new_main_tags_for_domain = [
                        udt
                        for udt in items_to_create
                        if udt.domain_id == domain.id
                    ]

                    if not new_main_tags_for_domain:
                        continue

                    current_main_count = (
                        User_Domain_Tag.objects.filter(
                            domain=domain,
                            user__role__code__in=[
                                "admin",
                                "super_admin",
                            ],
                            deleted_at__isnull=True,
                        ).count()
                    )

                    if (
                        current_main_count
                        + len(new_main_tags_for_domain)
                        > self.MAX_MAIN_TAGS_PER_DOMAIN
                    ):
                        log_critical_event(
                            action="BULK_SYNC_DOMAIN_TAGS",
                            status_type="failed",
                            request=request,
                            user_id=user.id,
                            error_code=60,
                            extra={
                                "reason": "main_tag_limit_race_condition",
                                "domain_name": domain.domain_name,
                            },
                        )
                        return Response(
                            {
                                "error_code": 60,
                                "message": {
                                    "fa": (
                                        f"دامنه «{domain.domain_name}» "
                                        "در همین فاصله به سقف ۲ تگ اصلی "
                                        "رسیده است."
                                    ),
                                    "en": (
                                        f"Domain «{domain.domain_name}» "
                                        "has reached the maximum of "
                                        "2 main tags."
                                    ),
                                },
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            # --------------------------------------------------------
            # DELETE
            # --------------------------------------------------------

            if ids_to_delete:
                User_Domain_Tag.objects.filter(
                    id__in=ids_to_delete
                ).update(
                    deleted_at=timezone.now()
                )

            # --------------------------------------------------------
            # UPDATE
            # --------------------------------------------------------

            if items_to_update:
                User_Domain_Tag.objects.bulk_update(
                    items_to_update,
                    fields=[
                        "tag",
                        "updated_at",
                    ],
                )

            # --------------------------------------------------------
            # ADD
            # --------------------------------------------------------

            if items_to_create:
                User_Domain_Tag.objects.bulk_create(
                    items_to_create
                )

        # ============================================================
        # 9. SUCCESS
        # ============================================================

        log_critical_event(
            action="BULK_SYNC_DOMAIN_TAGS",
            status_type="success",
            request=request,
            user_id=user.id,
            extra={
                "is_admin": is_admin,
                "added": len(items_to_create),
                "updated": len(items_to_update),
                "deleted": len(ids_to_delete),
            },
        )

        return Response(
            {
                "message": {
                    "fa": "تمام تغییرات با موفقیت ذخیره شدند.",
                    "en": "All changes were saved successfully.",
                },
                "result": {
                    "added": len(items_to_create),
                    "updated": len(items_to_update),
                    "deleted": len(ids_to_delete),
                },
            },
            status=status.HTTP_200_OK,
        )

