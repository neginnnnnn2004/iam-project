from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView

from identity.models import UserGroup, Domain, Tag, User_Domain_Tag
from identity.permissions import IsAdminRole
from identity.serializers.domain_serializers import (DomainRegisterSerializer ,TagRegisterSerializer ,UserDomainTagSerializer ,UserDomainTagPatchSerializer)

from drf_yasg.utils import swagger_auto_schema


# 1 import and update domain by admin (Bulk Enabled)
class ImportDomainView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @swagger_auto_schema(
        operation_description="""
        اضافه کردن دسته‌جمعی دامنه‌ها (Bulk Import)
        """,
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
                domain_instance = Domain(**validated_data)
                domains_to_create.append((domain_instance, groups))

            with transaction.atomic():
                created_instances = Domain.objects.bulk_create(
                    [item[0] for item in domains_to_create]
                )
                for instance, groups in zip(created_instances, [item[1] for item in domains_to_create]):
                    if groups:
                        instance.groups.set(groups)

            return Response(
                DomainRegisterSerializer(created_instances, many=True).data,
                status=status.HTTP_201_CREATED
            )
        else:
            domain = serializer.save()
            return Response(DomainRegisterSerializer(domain).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="""
        ویرایش دسته‌جمعی مشخصات دامنه‌ها و گروه‌های آن‌ها

        در بدنه درخواست باید برای هر دامنه، شناسه 'id' آن ارسال شود.
        """,
        request_body=DomainRegisterSerializer(many=True),
        responses={
            200: "Domains updated successfully",
            400: "Bad Request (Code 10)"
        }
    )
    def put(self, request):
        data = request.data
        if not isinstance(data, list):
            return Response({
                "error_code": 10,
                "message": "فرمت داده‌ها باید به صورت یک آرایه (لیست) باشد."
            }, status=status.HTTP_400_BAD_REQUEST)

        updated_domains = []
        errors = {}

        with transaction.atomic():
            for index, item in enumerate(data):
                domain_id = item.get('id')
                if not domain_id:
                    errors[f"item_{index}"] = "ارسال فیلد id برای ویرایش الزامی است."
                    continue

                try:
                    domain_instance = Domain.objects.get(id=domain_id)
                except Domain.DoesNotExist:
                    errors[f"item_{index}"] = f"دامنه با شناسه {domain_id} یافت نشد."
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

        return Response(
            {
                "message": f"مشخصات تعداد {len(updated_domains)} دامنه با موفقیت بروزرسانی شد.",
                "data": DomainRegisterSerializer(updated_domains, many=True).data
            },
            status=status.HTTP_200_OK
        )

#2 list of all domains
class DomainDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="دریافت لیست دامنه ها",
        responses={
            200: DomainRegisterSerializer(many=True),
            401: "Unauthorized",
        }
    )
    def get(self, request):
        user = request.user
        is_admin = (
            user.role is not None and
            user.role.code in ['admin', 'super_admin']
        )
        if is_admin or user.is_superuser:
            domains = Domain.objects.all()
        else:
            user_groups = UserGroup.objects.filter(user=user).values_list('groups', flat=True)

            domains =Domain.objects.filter(
                Q(groups__in=user_groups) |
                Q(groups = None)
            ).distinct()
        serializer = DomainRegisterSerializer(domains, many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)

#3 create tags
class CreateTagView(APIView):
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

#4 list of all tags
class TagDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="لیست تمامی تگ ها",
        responses={
            200: TagRegisterSerializer(many=True),
            401: "Unauthorized",
        }
    )

    def get(self, request):
        tag = Tag.objects.all()
        serializer = TagRegisterSerializer(tag , many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)


# 5 Assign a tag to domain by a user
class AssignTagToDomainView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""
        انتساب تگ/تگ ها به دامنه‌های موجود

        کدهای خطای اختصاصی :
        - code 10: اطلاعات ارسالی ناقص یا فرمت آرایه اشتباه است.
        - code 60: یک یا چند دامنه از قبل دارای تگ هستند .
        """,
        request_body=UserDomainTagSerializer(many=True),
        responses={
            201: UserDomainTagSerializer(many=True),
            400: "Bad Request (Code 10)",
            401: "Unauthorized",
            409: "Conflict (Code 60)",
        }
    )
    def post(self, request):
        serializer = UserDomainTagSerializer(
            data=request.data,
            context={'request': request},
            many=True
        )
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ثبت تگ‌ها معتبر نیست.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        items_to_create = []
        conflicts = []

        for item in serializer.validated_data:
            domain = item["domain"]
            tag = item["tag"]

            existing = User_Domain_Tag.objects.filter(user=user, domain=domain).first()
            if existing:
                conflicts.append(f"دامنه «{domain.domain_name}» از قبل تگ دارد.")
            else:
                items_to_create.append(User_Domain_Tag(user=user, domain=domain, tag=tag))

        if conflicts:
            return Response(
                {
                    "error_code": 60,
                    "message": "یک یا تعدادی از دامنه‌ها از قبل دارای تگ هستند. عملیات متوقف شد.",
                    "detail": {"conflicts": conflicts},
                },
                status=status.HTTP_409_CONFLICT
            )

        with transaction.atomic():
            User_Domain_Tag.objects.bulk_create(items_to_create)

        return Response(
            {
                "message": f"تعداد {len(items_to_create)} تگ با موفقیت برای دامنه‌ها ثبت شد.",
                "data": UserDomainTagSerializer(items_to_create, many=True).data
            },
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="""
        ویرایش دسته‌جمعی تگ دامنه‌ها با مکانیزم confirm

        کدهای خطای اختصاصی :
        - code 10: اطلاعات ارسالی ناقص یا فرمت آرایه اشتباه است.
        - code 61: دامنه‌ای جهت ویرایش فرستاده شده که از قبل تگی ندارد.
        - code 21: تغییر تگ دامنه‌ها نیاز به تایید نهایی کاربر دارد.
        """,
        request_body=UserDomainTagPatchSerializer(many=True),
        responses={
            200: UserDomainTagSerializer(many=True),
            400: "Bad Request (Code 10)",
            404: "Not Found (Code 61)",
            409: "Conflict (Code 21)",
        }
    )
    def patch(self, request):
        serializer = UserDomainTagPatchSerializer(
            data=request.data,
            context={'request': request},
            many=True
        )
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی برای ویرایش تگ‌ها معتبر نیست.",
                "detail": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        requires_confirm_list = []
        records_to_update = []
        not_found_domains = []

        for item in serializer.validated_data:
            domain = item["domain"]
            new_tag = item["tag"]
            confirm = item.get("confirm", False)

            existing = User_Domain_Tag.objects.filter(user=user, domain=domain).first()
            if not existing:
                not_found_domains.append(domain.domain_name)
                continue

            if existing.tag == new_tag:
                continue

            if not confirm:
                requires_confirm_list.append({
                    "domain_name": domain.domain_name,
                    "old_tag": existing.tag.title,
                    "new_tag": new_tag.title
                })
            else:
                existing.tag = new_tag
                records_to_update.append(existing)

        if not_found_domains:
            return Response(
                {
                    "error_code": 61,
                    "message": "برای دامنه‌های زیر تگی ثبت نشده است که مایل به تغییر آن باشید?.",
                    "detail": {"domains": not_found_domains}
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if requires_confirm_list:
            return Response(
                {
                    "error_code": 21,
                    "message": "تغییر تگ برای دامنه‌های زیر نیاز به تایید نهایی دارد.",
                    "detail": {
                        "requires_confirmation": True,
                        "conflicts": requires_confirm_list
                    }
                },
                status=status.HTTP_409_CONFLICT
            )

        if records_to_update:
            with transaction.atomic():
                for record in records_to_update:
                    record.save(update_fields=['tag', 'updated_at'])

        return Response(
            {
                "message": f"تعداد {len(records_to_update)} تگ با موفقیت به‌روزرسانی شد.",
                "data": UserDomainTagSerializer(records_to_update, many=True).data
            },
            status=status.HTTP_200_OK
        )