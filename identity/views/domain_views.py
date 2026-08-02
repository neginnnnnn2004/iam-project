from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView

from identity.models import UserGroup, Domain, Tag, User_Domain_Tag
from identity.permissions import IsAdminRole,IsAllowedUser
from identity.serializers.domain_serializers import (DomainRegisterSerializer ,TagRegisterSerializer ,UserDomainTagSerializer , TagListSerializer)

from drf_yasg.utils import swagger_auto_schema


# 1 import and update domain by admin (Bulk & Single Enabled)
class ImportOrEditDomainView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="اضافه کردن دسته‌جمعی یا تکی دامنه‌ها (Bulk/Single Import)",
        request_body=DomainRegisterSerializer(many=True),
        responses={
            201: DomainRegisterSerializer(many=True),
            400: "Bad Request (Code 10)"
        }
    )
    def post(self, request):
        data = request.data
        is_many = isinstance(data, list)
        serializer = DomainRegisterSerializer(data=data, many=is_many)

        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ایمپورت دامنه معتبر نیست.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        if is_many:
            domains_to_create = []
            for validated_data in serializer.validated_data:
                groups = validated_data.pop('groups', [])
                domain_instance = Domain(**validated_data, created_by=request.user)
                domains_to_create.append((domain_instance, groups))

            with transaction.atomic():
                created_instances = Domain.objects.bulk_create(
                    [item[0] for item in domains_to_create]
                )
                for instance, groups in zip(created_instances, [item[1] for item in domains_to_create]):
                    if groups:
                        instance.groups.set(groups)
                    instance.created_by = request.user

            return Response(
                DomainRegisterSerializer(created_instances, many=True).data,
                status=status.HTTP_201_CREATED
            )
        else:
            domain = serializer.save(created_by=request.user)
            return Response(DomainRegisterSerializer(domain).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="""
        ویرایش تکی یا دسته‌جمعی مشخصات دامنه‌ها (PATCH)

        - برای ویرایش تکی: یک Object ارسال کنید: {"domain_name": "a.com", "description": "new"}
        - برای ویرایش دسته‌جمعی: یک Array ارسال کنید: [{"domain_name": "a.com", ...}, ...]
        """,
        request_body=DomainRegisterSerializer(many=True),
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
                        errors[f"item_{index}"] = "ارسال فیلد domain_name برای ویرایش الزامی است."
                        continue

                    try:
                        domain_instance = Domain.objects.get(domain_name=domain_name)
                    except Domain.DoesNotExist:
                        errors[f"item_{index}"] = f"دامنه با نام «{domain_name}» یافت نشد."
                        continue

                    serializer = DomainRegisterSerializer(domain_instance, data=item, partial=True)
                    if not serializer.is_valid():
                        errors[f"item_{index}"] = serializer.errors
                        continue

                    updated_instance = serializer.save()
                    updated_domains.append(updated_instance)

            if errors:
                transaction.set_rollback(True)
                return Response({
                    "error_code": 10,
                    "message": "برخی از اطلاعات ارسالی برای ویرایش نامعتبر هستند.",
                    "detail": errors
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "message": f"مشخصات تعداد {len(updated_domains)} دامنه با موفقیت بروزرسانی شد.",
                "data": DomainRegisterSerializer(updated_domains, many=True).data
            }, status=status.HTTP_200_OK)

        else:
            domain_name = data.get('domain_name')
            if not domain_name:
                return Response({
                    "error_code": 10,
                    "message": "ارسال فیلد domain_name در بدنه درخواست الزامی است."
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                domain = Domain.objects.get(domain_name=domain_name)
            except Domain.DoesNotExist:
                return Response({
                    "error": f"دامنه‌ای با نام «{domain_name}» یافت نشد."
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = DomainRegisterSerializer(domain, data=data, partial=True)
            if not serializer.is_valid():
                return Response({
                    "error_code": 10,
                    "message": "اطلاعات ارسالی معتبر نیست.",
                    "detail": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            updated_domain = serializer.save()
            return Response(DomainRegisterSerializer(updated_domain).data, status=status.HTTP_200_OK)

#2 List of All Domains with Tag Visibility Logic
class DomainDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="دریافت لیست دامنه‌ها به همراه تگ‌های مجاز و وضعیت قابلیت افزودن تگ",
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

            # 🟢 1. تگ‌های اصلی: تگ‌هایی که توسط یک ادمین روی دامنه ست شده‌اند
            main_tags = [
                udt.tag for udt in domain_tags_qs
                if udt.user and udt.user.role and udt.user.role.code in ['admin', 'super_admin']
            ]
            has_main_tag = len(main_tags) > 0

            # 🟢 2. تگ‌های خودِ این کاربر جاری
            user_tags = [
                udt.tag for udt in domain_tags_qs
                if udt.user == user
            ]
            has_user_tag = len(user_tags) > 0

            # 🟢 3. پیاده‌سازی دقیقا بر اساس نقش‌ها
            if is_admin:
                # ادمین همه‌چیز را می‌بیند
                visible_tags = [udt.tag for udt in domain_tags_qs]
                can_add_tag = True

            elif is_limited:
                # کاربر محدود فقط تگ‌های اصلی را می‌بیند و اجازه افزودن ندارد
                visible_tags = main_tags
                can_add_tag = False

            elif has_main_tag:
                # اگر دامنه تگ اصلی داشته باشد، کاربر عادی فقط تگ‌های اصلی را می‌بیند
                visible_tags = main_tags
                can_add_tag = False

            else:
                # 🎯 نیازمندی 5.11: کاربر عادی فقط تگ‌های خودش + تگ‌های اصلی را می‌بیند (نه کاربران دیگر)
                # ترکیب تگ‌های اصلی و تگ‌های خود کاربر (بدون تکرار)
                unique_tags_dict = {t.id: t for t in (main_tags + user_tags)}
                visible_tags = list(unique_tags_dict.values())

                # اگر کاربر قبلاً خودش رو این دامنه تگ نزده باشد، می‌تواند تگ اضافه کند
                can_add_tag = not has_user_tag

            # سریالایز و ساخت خروجی
            domain_data = DomainRegisterSerializer(domain).data
            domain_data['tags'] = TagListSerializer(visible_tags, many=True).data
            domain_data['can_add_tag'] = can_add_tag
            domain_data['has_main_tag'] = has_main_tag

            result.append(domain_data)


#3 create tags
class TagListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="""
            ایجاد تگ جدید

            کدهای خطای اختصاصی :
            - code 10: اطلاعات ارسالی ناقص یا اشتباه است.
            """,
        request_body=TagRegisterSerializer,
        responses={
            201: TagRegisterSerializer(),
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
        }
    )
    def post(self, request):
        serializer = TagRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ایجاد تگ معتبر نیست.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        tag = serializer.save(created_by=request.user)
        return Response(TagRegisterSerializer(tag).data, status=status.HTTP_201_CREATED)

# 4 edit or delete the tag
class TagDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, pk):
        try:
            return Tag.objects.get(pk=pk)
        except Tag.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_description="""
ویرایش تگ بر اساس شناسه               
               کدهای خطای اختصاصی :
               - code 10: اطلاعات ارسالی ناقص یا اشتباه است.
               - code 55: تگ مورد نظر یافت نشد.

               """,
        request_body=TagRegisterSerializer,
        responses={
            200: TagRegisterSerializer(),
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 55)"
        }
    )
    def patch(self, request, pk):
        tag = self.get_object(pk)
        if not tag:
            return Response({
            "error_code": 55,
                "message": f"تگی با شناسه {pk} یافت نشد.",
                }, status = status.HTTP_404_NOT_FOUND)
        serializer = TagRegisterSerializer(tag, data=request.data,partial=True)
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی معتبر نیست.",
                "detail": serializer.errors
            },status=status.HTTP_400_BAD_REQUEST)

        updated_tag = serializer.save()
        return Response(TagRegisterSerializer(updated_tag).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""
            حذف نرم تگ توسط ادمین / سوپرادمین بر اساس شناسه
            
            کدهای خطای اختصاصی :
            - code 55: تگ مورد نظر یافت نشد.
            """,
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found (Code 55)"
        }
    )
    def delete(self, request,pk):
        tag = self.get_object(pk)
        if not tag:
            return Response({
                "error_code": 55,
                "message": f"تگی با شناسه {pk} یافت نشد.",
            },status=status.HTTP_404_NOT_FOUND)

        tag.deleted_at = timezone.now()
        tag.is_active = False
        tag.save(update_fields=["is_active", 'deleted_at'])

        return Response(status=status.HTTP_204_NO_CONTENT)



#5 list of all tags
class ListOfTagView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="لیست تمامی تگ های فعال جهت انتخاب توسط کاربر",
        responses={
            200: TagListSerializer(many=True),
            401: "Unauthorized",
        }
    )

    def get(self, request):
        tags= Tag.objects.filter(is_active=True,deleted_at__isnull=True).order_by('title')
        serializer = TagListSerializer(tags , many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)


# 6. Assign / Update / Delete Tags Bulk Sync
class AssignTagToDomainView(APIView):
    permission_classes = [IsAuthenticated, IsAllowedUser]

    def _check_user_access(self, user):
        """بررسی سطح دسترسی کاربران محدود شده"""
        role_code = user.role.code if user.role else None
        if role_code in ['limited']:
            return False, Response({
                "error_code": 403,
                "message": "کاربران محدودشده امکان افزودن، ویرایش یا حذف تگ را ندارند."
            }, status=status.HTTP_403_FORBIDDEN)
        return True, None

    def _get_domain_by_name(self, domain_name, index):
        """یافتن دامنه صرفاً بر اساس domain_name"""
        if not domain_name:
            return None, f"آیتم {index}: نام دامنه (domain_name) ارسال نشده است."
        try:
            return Domain.objects.get(domain_name=domain_name, deleted_at__isnull=True), None
        except Domain.DoesNotExist:
            return None, f"آیتم {index}: دامنه‌ای با نام «{domain_name}» یافت نشد."

    def _get_tag_by_title(self, title, index):
        """یافتن تگ صرفاً بر اساس title"""
        if not title:
            return None, f"آیتم {index}: عنوان تگ (title) ارسال نشده است."
        try:
            return Tag.objects.get(title=title, is_active=True, deleted_at__isnull=True), None
        except Tag.DoesNotExist:
            return None, f"آیتم {index}: تگی با عنوان «{title}» یافت نشد یا غیرفعال است."

    # =========================================================================
    # 1. POST: اختصاص و اضافه کردن تگ جدید (Bulk Create)
    # =========================================================================
    @swagger_auto_schema(
        operation_description="افزودن دسته‌جمعی تگ‌های جدید به دامنه‌ها با domain_name و title",
        request_body=UserDomainTagSerializer(many=True),
        responses={200: "تگ‌/ تگ های با موفقیت اضافه شدند.", 400: "Bad Request (Code 60)", 403: "Forbidden"}
    )
    def post(self, request):
        has_access, response = self._check_user_access(request.user)
        if not has_access:
            return response

        user = request.user
        is_admin = user.is_superuser or (user.role.code in ['admin', 'super_admin'] if user.role else False)
        items = request.data if isinstance(request.data, list) else [request.data]

        items_to_create = []
        errors = []
        pending_creations_per_domain = {}

        for index, item in enumerate(items):
            domain_name = item.get("domain_name")
            title = item.get("title")

            # 1. یافتن دامنه بر اساس نام
            domain, err = self._get_domain_by_name(domain_name, index)
            if err:
                errors.append(err)
                continue

            # نیازمندی 5.12: عدم اجازه اضافه کردن تگ برای کاربر عادی در صورت وجود main_tag
            has_main_tag = User_Domain_Tag.objects.filter(
                domain=domain,
                tag__created_by__role__code__in=['admin', 'super_admin']
            ).exists()

            if has_main_tag and not is_admin:
                errors.append(f"دامنه «{domain.domain_name}» دارای برچسب اصلی است و امکان افزودن برچسب جدید ندارد.")
                continue

            # 2. یافتن تگ بر اساس عنوان
            tag, err = self._get_tag_by_title(title, index)
            if err:
                errors.append(err)
                continue

            user_existing_udts = list(User_Domain_Tag.objects.filter(user=user, domain=domain))

            # جلوگیری از اضافه کردن تگ تکراری
            if any(udt.tag_id == tag.id for udt in user_existing_udts):
                errors.append(f"تگ «{tag.title}» قبلاً توسط شما برای دامنه «{domain.domain_name}» ثبت شده است.")
                continue

            # بررسی سقف تگ (ادمین: ۲ | کاربر عادی: ۱)
            max_allowed_tags = 2 if is_admin else 1
            pending_creations = pending_creations_per_domain.get(domain.id, 0)
            effective_tag_count = len(user_existing_udts) + pending_creations

            if effective_tag_count >= max_allowed_tags:
                errors.append(f"دامنه «{domain.domain_name}»: به سقف مجاز انتخاب تگ ({max_allowed_tags}) رسیده است.")
                continue

            items_to_create.append(User_Domain_Tag(user=user, domain=domain, tag=tag))
            pending_creations_per_domain[domain.id] = pending_creations + 1

        if errors:
            return Response({"error_code": 60, "message": "خطا در افزودن تگ‌ها.", "detail": errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if items_to_create:
                User_Domain_Tag.objects.bulk_create(items_to_create)

        return Response({"message": "تگ‌های جدید با موفقیت اضافه شدند."}, status=status.HTTP_200_OK)

    # =========================================================================
    # 2. PATCH: ویرایش و جایگزینی تگ موجود (Bulk Update)
    # =========================================================================
    @swagger_auto_schema(
        operation_description="ویرایش دسته‌جمعی تگ‌های دامنه‌ها بر اساس domain_name و title (نیاز به confirm برای کاربر عادی)",
        request_body=UserDomainTagSerializer(many=True),
        responses={200: "ویرایش با موفقیت انجام شد.", 409: "Conflict (Code 21)", 400: "Bad Request"}
    )
    def patch(self, request):
        has_access, response = self._check_user_access(request.user)
        if not has_access:
            return response

        user = request.user
        is_admin = user.is_superuser or (user.role.code in ['admin', 'super_admin'] if user.role else False)
        items = request.data if isinstance(request.data, list) else [request.data]

        requires_confirm_list = []
        items_to_update = []
        errors = []

        for index, item in enumerate(items):
            domain_name = item.get("domain_name")
            title = item.get("title")
            confirm = item.get("confirm", False)

            # 1. یافتن دامنه بر اساس نام
            domain, err = self._get_domain_by_name(domain_name, index)
            if err:
                errors.append(err)
                continue

            # دریافت تگ‌های موجود همین کاربر برای این دامنه
            user_existing_udts = list(User_Domain_Tag.objects.filter(user=user, domain=domain))

            if not user_existing_udts:
                errors.append(f"دامنه «{domain.domain_name}»: تگی برای ویرایش وجود ندارد. ابتدا تگ اضافه کنید.")
                continue

            # 🟢 تغییر اصلی در بررسی main_tag:
            # چک می‌کنیم آیا این دامنه تگ ادمینی دارد که متعلق به یک ادمین *دیگر* باشد؟
            # اگر خود فاطمه هم ادمین نباشد و تگ‌های ادمین روی دامنه وجود داشته باشند، بلاک می‌شود.
            has_main_tag = User_Domain_Tag.objects.filter(
                domain=domain,
                user__role__code__in=['admin', 'super_admin']
            ).exclude(user=user).exists()  # 👈 exclude(user=user) اضافه شد!

            if has_main_tag and not is_admin:
                errors.append(f"دامنه «{domain.domain_name}» دارای برچسب اصلی است و امکان تغییر تگ ندارد.")
                continue

            # 2. یافتن تگ جدید بر اساس عنوان
            tag, err = self._get_tag_by_title(title, index)
            if err:
                errors.append(err)
                continue

            existing_udt = user_existing_udts[0]  # تگ فعلی کاربر

            if existing_udt.tag_id == tag.id:
                errors.append(
                    f"دامنه «{domain.domain_name}»: تگ انتخاب شده («{tag.title}») هم‌اکنون برای شما فعال است و تغییری ایجاد نشد.")
                continue

            # نیازمندی 5.8: دریافت تاییدیه برای ویرایش تگ کاربر عادی
            if not is_admin and not confirm:
                requires_confirm_list.append({
                    "domain_name": domain.domain_name,
                    "old_tag": existing_udt.tag.title,
                    "new_tag": tag.title
                })
            else:
                existing_udt.tag = tag
                items_to_update.append(existing_udt)

        if errors:
            return Response({"error_code": 60, "message": "خطا در ویرایش تگ‌ها.", "detail": errors},
                            status=status.HTTP_400_BAD_REQUEST)

        # ارسال هشدار 409 و دریافت تاییدیه از کاربر
        if requires_confirm_list:
            return Response({
                "error_code": 21,
                "message": "ویرایش برخی تگ‌ها نیاز به تایید نهایی دارد.",
                "detail": {
                    "requires_confirmation": True,
                    "conflicts": requires_confirm_list
                }
            }, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            if items_to_update:
                User_Domain_Tag.objects.bulk_update(items_to_update, fields=['tag', 'updated_at'])

        return Response({"message": "ویرایش تگ‌ها با موفقیت انجام شد."}, status=status.HTTP_200_OK)
    # =========================================================================
    # 3. DELETE: حذف تگ‌ها (Bulk Delete)
    # =========================================================================
    @swagger_auto_schema(
        operation_description="حذف دسته‌جمعی تگ‌های کاربر روی دامنه‌ها بر اساس domain_name و title",
        request_body=UserDomainTagSerializer(many=True),
        responses={200: "تگ‌ها با موفقیت حذف شدند.", 400: "Bad Request"}
    )
    def delete(self, request):
        has_access, response = self._check_user_access(request.user)
        if not has_access:
            return response

        user = request.user
        items = request.data if isinstance(request.data, list) else [request.data]
        ids_to_delete = []
        errors = []

        for index, item in enumerate(items):
            domain_name = item.get("domain_name")
            title = item.get("title")

            # 1. یافتن دامنه بر اساس نام
            domain, err = self._get_domain_by_name(domain_name, index)
            if err:
                errors.append(err)
                continue

            user_existing_udts = User_Domain_Tag.objects.filter(user=user, domain=domain)

            if not user_existing_udts.exists():
                continue

            # 2. اگر title فرستاده شد، همان تگ خاص حذف می‌شود؛ در غیر این صورت کل تگ‌های کاربر روی آن دامنه
            if title:
                tag, err = self._get_tag_by_title(title, index)
                if err:
                    errors.append(err)
                    continue
                udts = user_existing_udts.filter(tag=tag)
                ids_to_delete.extend(udts.values_list('id', flat=True))
            else:
                ids_to_delete.extend(user_existing_udts.values_list('id', flat=True))

        if errors:
            return Response({"error_code": 60, "message": "خطا در حذف تگ‌ها.", "detail": errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if ids_to_delete:
                User_Domain_Tag.objects.filter(id__in=ids_to_delete).delete()

        return Response({"message": "تگ‌های انتخابی با موفقیت حذف شدند."}, status=status.HTTP_200_OK)