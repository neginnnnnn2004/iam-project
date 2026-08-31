# from urllib.parse import urlparse
# from django.utils import timezone
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
#
# from django.db import transaction
# from django.db.models import Q
# from rest_framework.views import APIView
#
# from identity.models import UserGroup, Domain, Tag, User_Domain_Tag
# from identity.permissions import IsAdminRole,IsAllowedUser
# from identity.serializers.domain_serializers import (DomainRegisterSerializer ,TagRegisterSerializer ,UserDomainTagSerializer , TagListSerializer,UserDomainTagPatchSerializer)
#
# from drf_yasg.utils import swagger_auto_schema
#
#
# def extract_root_domain(url_or_domain: str) -> str:
#     url_or_domain = url_or_domain.strip().lower()
#
#     if not url_or_domain.startswith(("http://", "https://")):
#         url_or_domain = "http://" + url_or_domain
#
#     parsed = urlparse(url_or_domain)
#     domain_name = parsed.netloc or parsed.path
#
#     domain_name = domain_name.split(":")[0]
#
#     parts = domain_name.split(".")
#     if len(parts) > 2:
#         return ".".join(parts[-2:])
#     return domain_name
#
# # 1 import and update domain by admin (Bulk & Single Enabled)
# class ImportOrEditDomainView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     @swagger_auto_schema(
#         operation_description="Bulk or single addition of domains with admin access (automatic validation, duplicate removal, and root domain extraction)",
#         request_body=DomainRegisterSerializer(many=True),
#         responses={
#             201: DomainRegisterSerializer(many=True),
#             400: "Bad Request (Code 10)"
#         }
#     )
#     def post(self, request):
#         raw_data = request.data
#         is_many = isinstance(raw_data, list)
#         items = raw_data if is_many else [raw_data]
#
#         existing_domains = set(
#             Domain.objects.filter(deleted_at__isnull=True)
#             .values_list('domain_name', flat=True)
#         )
#
#         seen_in_request = set()
#         cleaned_items = []
#         skipped_domains = []
#
#         for item in items:
#             original_name = item.get('domain_name', '')
#             if not original_name:
#                 continue
#
#             root_domain = extract_root_domain(original_name)
#
#             if root_domain in existing_domains or root_domain in seen_in_request:
#                 skipped_domains.append(original_name)
#                 continue
#
#             seen_in_request.add(root_domain)
#             item_copy = item.copy()
#             item_copy['domain_name'] = root_domain
#             cleaned_items.append(item_copy)
#
#         if not cleaned_items:
#             return Response({
#                 "message": {
#                     "fa": "تمامی دامنه‌های ارسالی تکراری بوده و از فرآیند ثبت حذف شدند.",
#                     "en": "All submitted domains were duplicates and removed from the registration process.",
#                 },
#                 "skipped_domains": skipped_domains,
#                 "created_domains": []
#             }, status=status.HTTP_200_OK)
#
#         serializer = DomainRegisterSerializer(data=cleaned_items, many=True)
#
#         if not serializer.is_valid():
#             return Response({
#                 "error_code": 10,
#                 "message": {
#                     "fa": "اطلاعات ارسالی برای ایمپورت دامنه معتبر نیست.",
#                     "en": "The submitted data for domain import is not valid.",
#                 },
#                 "detail": serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         domains_to_create = []
#         for validated_data in serializer.validated_data:
#             groups = validated_data.pop('groups', [])
#             domain_instance = Domain(**validated_data, created_by=request.user)
#             domains_to_create.append((domain_instance, groups))
#
#         with transaction.atomic():
#             created_instances = Domain.objects.bulk_create(
#                 [item[0] for item in domains_to_create]
#             )
#             for instance, groups in zip(created_instances, [item[1] for item in domains_to_create]):
#                 if groups:
#                     instance.groups.set(groups)
#
#         created_data = DomainRegisterSerializer(created_instances, many=True).data
#
#         response_payload = {
#             "message": {
#                 "fa": "فرآیند ایمپورت با موفقیت انجام شد.",
#                 "en": "The import process completed successfully.",
#             },
#             "created_count": len(created_instances),
#             "skipped_count": len(skipped_domains),
#             "skipped_domains": skipped_domains,
#             "created_domains": created_data
#         }
#
#         return Response(
#             response_payload if is_many else (created_data[0] if created_data else {}),
#             status=status.HTTP_201_CREATED
#         )
#
#     @swagger_auto_schema(
#         operation_description="""
#         Edit domain information individually or in bulk, with admin access.
#
#         - For single update: Send an Object: {"domain_name": "a.com", "description": "new"}
#         - For bulk update: Send an Array: [{"domain_name": "a.com", ...}, ...]
#         """,
#         request_body=DomainRegisterSerializer(many=True),
#         responses={
#             200: "Domains updated successfully",
#             400: "Bad Request (Code 10)"
#         }
#     )
#     def patch(self, request):
#         data = request.data
#
#         if isinstance(data, list):
#             updated_domains = []
#             errors = {}
#
#             with transaction.atomic():
#                 for index, item in enumerate(data):
#                     domain_name = item.get('domain_name')
#                     if not domain_name:
#                         errors[f"item_{index}"] = {
#                             "fa": "ارسال فیلد domain_name برای ویرایش الزامی است.",
#                             "en": "The domain_name field is required for editing."
#                         }
#                         continue
#
#                     try:
#                         domain_instance = Domain.objects.get(domain_name=domain_name)
#                     except Domain.DoesNotExist:
#                         errors[f"item_{index}"] = {
#                             "fa": f"دامنه با نام «{domain_name}» یافت نشد.",
#                             "en": f"Domain with name «{domain_name}» was not found."
#                         }
#                         continue
#
#                     serializer = DomainRegisterSerializer(domain_instance, data=item, partial=True)
#                     if not serializer.is_valid():
#                         errors[f"item_{index}"] = serializer.errors
#                         continue
#
#                     updated_instance = serializer.save()
#                     updated_domains.append(updated_instance)
#
#                 if errors:
#                     transaction.set_rollback(True)
#                     return Response({
#                         "error_code": 10,
#                         "message": {
#                             "fa": "برخی از اطلاعات ارسالی برای ویرایش نامعتبر هستند.",
#                             "en": "Some of the submitted data for editing is invalid."
#                         },
#                         "detail": errors
#                     }, status=status.HTTP_400_BAD_REQUEST)
#
#             return Response({
#                 "message": {
#                     "fa": f"مشخصات تعداد {len(updated_domains)} دامنه با موفقیت بروزرسانی شد.",
#                     "en": f"Details of {len(updated_domains)} domain(s) were updated successfully."
#                 },
#                 "data": DomainRegisterSerializer(updated_domains, many=True).data
#             }, status=status.HTTP_200_OK)
#
#         else:
#             domain_name = data.get('domain_name')
#             if not domain_name:
#                 return Response({
#                     "error_code": 10,
#                     "message": {
#                         "fa": "ارسال فیلد domain_name در بدنه درخواست الزامی است.",
#                         "en": "The domain_name field is required in the request body."
#                     },
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#             try:
#                 domain = Domain.objects.get(domain_name=domain_name)
#             except Domain.DoesNotExist:
#                 return Response({
#                     "error": {
#                         "fa": f"دامنه‌ای با نام «{domain_name}» یافت نشد.",
#                         "en": f"Domain with name «{domain_name}» was not found."
#                     },
#                 }, status=status.HTTP_404_NOT_FOUND)
#
#             serializer = DomainRegisterSerializer(domain, data=data, partial=True)
#             if not serializer.is_valid():
#                 return Response({
#                     "error_code": 10,
#                     "message": {
#                         "fa": "اطلاعات ارسالی معتبر نیست.",
#                         "en": "The submitted data is not valid."
#                     },
#                     "detail": serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#             updated_domain = serializer.save()
#             return Response(DomainRegisterSerializer(updated_domain).data, status=status.HTTP_200_OK)
#
# #2 List of All Domains with Tag Visibility Logic
# class DomainDetailView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     @swagger_auto_schema(
#         operation_description="Retrieve the list of domains along with allowed tags and the tag-addition availability status",
#         responses={
#             200: DomainRegisterSerializer(many=True),
#             401: "Unauthorized",
#             403: "Forbidden"
#         }
#     )
#     def get(self, request):
#         user = request.user
#         role_code = user.role.code if user.role else None
#
#         is_admin = user.is_superuser or (role_code in ['admin', 'super_admin'])
#         is_limited = (role_code in ['limited', 'restricted'])
#
#         if is_admin:
#             domains = Domain.objects.filter(deleted_at__isnull=True)
#         else:
#             user_groups = UserGroup.objects.filter(user=user).values_list('group_id', flat=True)
#             domains = Domain.objects.filter(
#                 Q(groups__in=user_groups) | Q(groups__isnull=True),
#                 deleted_at__isnull=True
#             ).distinct()
#
#         result = []
#         for domain in domains:
#             domain_tags_qs = User_Domain_Tag.objects.filter(domain=domain).select_related('tag', 'user__role')
#
#             main_tags = [
#                 udt.tag for udt in domain_tags_qs
#                 if udt.user and udt.user.role and udt.user.role.code in ['admin', 'super_admin']
#             ]
#             has_main_tag = len(main_tags) > 0
#
#             user_tags = [
#                 udt.tag for udt in domain_tags_qs
#                 if udt.user == user
#             ]
#             has_user_tag = len(user_tags) > 0
#
#             if is_admin:
#                 visible_tags = [udt.tag for udt in domain_tags_qs]
#                 can_add_tag = True
#
#             elif is_limited:
#                 visible_tags = main_tags
#                 can_add_tag = False
#
#             elif has_main_tag:
#                 visible_tags = main_tags
#                 can_add_tag = False
#
#             else:
#                 unique_tags_dict = {t.id: t for t in (main_tags + user_tags)}
#                 visible_tags = list(unique_tags_dict.values())
#
#                 can_add_tag = not has_user_tag
#
#             domain_data = DomainRegisterSerializer(domain).data
#             domain_data['tags'] = TagListSerializer(visible_tags, many=True).data
#             domain_data['can_add_tag'] = can_add_tag
#             domain_data['has_main_tag'] = has_main_tag
#
#             result.append(domain_data)
#         return Response(result, status=status.HTTP_200_OK)
#
#
# #3 create tags
# class TagListCreateView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     @swagger_auto_schema(
#
#         operation_description="""
#         Create a new tag, with admin access.
#
#         Custom error codes:
#         - code 10: The submitted information is incomplete or invalid.
#         """,
#         request_body=TagRegisterSerializer,
#         responses={
#             201: TagRegisterSerializer(),
#             400: "Bad Request (Code 10)",
#             401: "Unauthorized",
#             403: "Forbidden",
#         }
#     )
#     def post(self, request):
#         serializer = TagRegisterSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response({
#                 "error_code": 10,
#                 "message": {
#                     "fa": "اطلاعات ارسالی برای ایجاد تگ معتبر نیست.",
#                     "en": "The submitted data for creating a tag is not valid."
#                 },
#                 "detail": serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         tag = serializer.save(created_by=request.user)
#         return Response(TagRegisterSerializer(tag).data, status=status.HTTP_201_CREATED)
#
# # 4 edit or delete the tag
# class TagDetailView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     def get_object(self, pk):
#         try:
#             return Tag.objects.get(pk=pk)
#         except Tag.DoesNotExist:
#             return None
#
#     @swagger_auto_schema(
#         operation_description="""
#         Edit a tag by ID, with admin access.
#
#         Custom error codes:
#         - code 10: The submitted information is incomplete or invalid.
#         - code 55: The requested tag was not found.
#         """,
#         request_body=TagRegisterSerializer,
#         responses={
#             200: TagRegisterSerializer(),
#             400: "Bad Request (Code 10)",
#             401: "Unauthorized",
#             403: "Forbidden",
#             404: "Not Found (Code 55)"
#         }
#     )
#     def patch(self, request, pk):
#         tag = self.get_object(pk)
#         if not tag:
#             return Response({
#             "error_code": 55,
#                 "message": {
#                     "fa": f"تگی با شناسه {pk} یافت نشد.",
#                     "en": f"Tag with ID {pk} was not found."
#                 },
#             }, status = status.HTTP_404_NOT_FOUND)
#
#         serializer = TagRegisterSerializer(tag, data=request.data,partial=True)
#         if not serializer.is_valid():
#             return Response({
#                 "error_code": 10,
#                 "message": {
#                     "fa": "اطلاعات ارسالی معتبر نیست.",
#                     "en": "The submitted data is not valid."
#                 },
#                 "detail": serializer.errors
#             },status=status.HTTP_400_BAD_REQUEST)
#
#         updated_tag = serializer.save()
#         return Response(TagRegisterSerializer(updated_tag).data, status=status.HTTP_200_OK)
#
#     @swagger_auto_schema(
#         operation_description="""
#         Soft-delete a tag by ID, with admin access.
#
#         Custom error codes:
#         - code 55: The requested tag was not found.
#         """,
#         responses={
#             204: "No Content",
#             401: "Unauthorized",
#             403: "Forbidden",
#             404: "Not Found (Code 55)"
#         }
#     )
#     def delete(self, request,pk):
#         tag = self.get_object(pk)
#         if not tag:
#             return Response({
#                 "error_code": 55,
#                 "message": {
#                     "fa": f"تگی با شناسه {pk} یافت نشد.",
#                     "en": f"Tag with ID {pk} was not found."
#                 },
#             },status=status.HTTP_404_NOT_FOUND)
#
#         tag.deleted_at = timezone.now()
#         tag.is_active = False
#         tag.save(update_fields=["is_active", 'deleted_at'])
#
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#
#
# #5 list of all tags
# class ListOfTagView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     @swagger_auto_schema(
#         operation_description="Retrieve a list of all active tags available for user selection",
#         responses={
#             200: TagListSerializer(many=True),
#             401: "Unauthorized",
#         }
#     )
#
#     def get(self,request):
#         tags= Tag.objects.filter(is_active=True,deleted_at__isnull=True).order_by('title')
#         serializer = TagListSerializer(tags , many=True)
#         return Response(serializer.data , status=status.HTTP_200_OK)
#
#
# # 6. Assign / Update / Delete Tags Bulk Sync
# class AssignTagToDomainView(APIView):
#     permission_classes = [IsAuthenticated, IsAllowedUser]
#
#     def _check_user_access(self, user):
#         """بررسی سطح دسترسی کاربران محدود شده"""
#         role_code = user.role.code if user.role else None
#         if role_code in ['limited']:
#             return False, Response({
#                 "error_code": 403,
#                 "message": {
#                     "fa": "کاربران محدودشده امکان افزودن، ویرایش یا حذف تگ را ندارند.",
#                     "en": "Restricted users are not allowed to add, edit, or delete tags."
#                 },
#             }, status=status.HTTP_403_FORBIDDEN)
#         return True, None
#
#     def _get_domain_by_name(self, domain_name, index):
#         """یافتن دامنه صرفاً بر اساس domain_name"""
#         if not domain_name:
#             return None, {
#                 "fa": f"آیتم {index}: دامنه‌ای با نام «{domain_name}» یافت نشد.",
#                 "en": f"Item {index}: Domain with name «{domain_name}» was not found."
#             }
#         try:
#             return Domain.objects.get(domain_name=domain_name, deleted_at__isnull=True), None
#         except Domain.DoesNotExist:
#             return None, {
#                 "fa": f"آیتم {index}: دامنه‌ای با نام «{domain_name}» یافت نشد.",
#                 "en": f"Item {index}: Domain with name «{domain_name}» was not found."
#             }
#
#     def _get_tag_by_title(self, title, index):
#         """یافتن تگ صرفاً بر اساس title"""
#         if not title:
#             return None, {
#                 "fa": f"آیتم {index}: عنوان تگ (title) ارسال نشده است.",
#                 "en": f"Item {index}: The tag title (title) was not provided."
#             }
#         try:
#             return Tag.objects.get(title=title, is_active=True, deleted_at__isnull=True), None
#         except Tag.DoesNotExist:
#             return None, {
#                 "fa": f"آیتم {index}: تگی با عنوان «{title}» یافت نشد یا غیرفعال است.",
#                 "en": f"Item {index}: Tag with title «{title}» was not found or is inactive."
#             }
#
#     # =========================================================================
#     # 1. POST: add & assign new tag (Bulk Create)
#     # =========================================================================
#     @swagger_auto_schema(
#         operation_description="Bulk addition of new tags to domains using domain_name and title",
#         request_body=UserDomainTagSerializer(many=True),
#         responses={
#             200: "tag/ tags added successfully",
#             400: "Bad Request (Code 60)",
#             403: "Forbidden"
#         }
#     )
#     def post(self, request):
#         has_access, response = self._check_user_access(request.user)
#         if not has_access:
#             return response
#
#         user = request.user
#         is_admin = user.is_superuser or (user.role.code in ['admin', 'super_admin'] if user.role else False)
#         items = request.data if isinstance(request.data, list) else [request.data]
#
#         items_to_create = []
#         errors = []
#         pending_creations_per_domain = {}
#
#         for index, item in enumerate(items):
#             domain_name = item.get("domain_name")
#             title = item.get("title")
#
#             domain, err = self._get_domain_by_name(domain_name, index)
#             if err:
#                 errors.append(err)
#                 continue
#
#             has_main_tag = User_Domain_Tag.objects.filter(
#                 domain=domain,
#                 user__role__code__in=['admin', 'super_admin'],
#                 deleted_at__isnull=True
#             ).exists()
#
#             if has_main_tag and not is_admin:
#                 errors.append({
#                     "fa": f"دامنه «{domain.domain_name}» دارای برچسب اصلی است و امکان افزودن برچسب جدید ندارد.",
#                     "en": f"Domain «{domain.domain_name}» has a primary tag and cannot have new tags added."
#                 })
#                 continue
#
#             tag, err = self._get_tag_by_title(title, index)
#             if err:
#                 errors.append(err)
#                 continue
#
#             user_existing_udts = list(User_Domain_Tag.objects.filter(user=user, domain=domain,deleted_at__isnull=True))
#
#             if any(udt.tag_id == tag.id for udt in user_existing_udts):
#                 errors.append({
#                     "fa": f"تگ «{tag.title}» قبلاً توسط شما برای دامنه «{domain.domain_name}» ثبت شده است.",
#                     "en": f"Tag «{tag.title}» has already been registered by you for domain «{domain.domain_name}»."
#                 })
#                 continue
#
#             max_allowed_tags = 2 if is_admin else 1
#             pending_creations = pending_creations_per_domain.get(domain.id, 0)
#             effective_tag_count = len(user_existing_udts) + pending_creations
#
#             if effective_tag_count >= max_allowed_tags:
#                 errors.append({
#                     "fa": f"دامنه «{domain.domain_name}»: به سقف مجاز انتخاب تگ ({max_allowed_tags}) رسیده است.",
#                     "en": f"Domain «{domain.domain_name}»: reached the maximum allowed tag limit ({max_allowed_tags})."
#                 })
#                 continue
#
#             items_to_create.append(User_Domain_Tag(user=user, domain=domain, tag=tag))
#             pending_creations_per_domain[domain.id] = pending_creations + 1
#
#         if errors:
#             return Response({
#                 "error_code": 60,
#                 "message": {
#                     "fa": "خطا در افزودن تگ‌ها.",
#                     "en": "Error in adding tags."
#                 },
#                 "detail": errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         with transaction.atomic():
#             if items_to_create:
#                 User_Domain_Tag.objects.bulk_create(items_to_create)
#
#         return Response({
#             "message": {
#                 "fa": "تگ‌های جدید با موفقیت اضافه شدند.",
#                 "en": "New tags were added successfully."
#             }
#         }, status=status.HTTP_200_OK)
#
#     # =========================================================================
#     # 2. PATCH: edit & replace the current tag (Bulk Update)
#     # =========================================================================
#     @swagger_auto_schema(
#         operation_description="Bulk update of domain tags using domain_name and title (confirmation required for regular users)",
#         request_body=UserDomainTagPatchSerializer(many=True),
#         responses={200: "edit is done successfully", 409: "Conflict (Code 21)", 400: "Bad Request"}
#     )
#     def patch(self, request):
#         has_access,  response = self._check_user_access(request.user)
#         if not has_access:
#             return response
#
#         user = request.user
#         items = request.data if isinstance(request.data, list) else [request.data]
#
#         requires_confirm_list = []
#         items_to_update = []
#         errors = []
#
#         for index, item in enumerate(items):
#             domain_name = item.get("domain_name")
#             title = item.get("title")
#             confirm = item.get("confirm", False)
#
#             domain, err = self._get_domain_by_name(domain_name, index)
#             if err:
#                 errors.append(err)
#                 continue
#
#             user_existing_udts = list(User_Domain_Tag.objects.filter(
#                 user=user,
#                 domain=domain,
#                 deleted_at__isnull = True
#             ))
#
#             if not user_existing_udts:
#                 errors.append({
#                     "fa": f"دامنه «{domain.domain_name}»: تگی متعلق به شما برای ویرایش وجود ندارد.",
#                     "en": f"Domain «{domain.domain_name}»: there is no tag belonging to you to edit."
#                 })
#                 continue
#
#             is_admin = user.is_superuser or (
#                 user.role.code in ['admin', 'super_admin'] if getattr(user, 'role', None) else False)
#
#             has_main_tag = User_Domain_Tag.objects.filter(
#                 domain=domain,
#                 user__role__code__in=['admin', 'super_admin'],
#                 deleted_at__isnull=True
#             ).exclude(user=user).exists()
#
#             if has_main_tag and not is_admin:
#                 errors.append({
#                     "fa": f"دامنه «{domain.domain_name}» دارای برچسب اصلی است و امکان تغییر تگ ندارد.",
#                     "en": f"Domain «{domain.domain_name}» has a primary tag and cannot have its tag changed."
#                 })
#                 continue
#
#             tag, err = self._get_tag_by_title(title, index)
#             if err:
#                 errors.append(err)
#                 continue
#
#             existing_udt = user_existing_udts[0]
#
#             if existing_udt.tag_id == tag.id:
#                 errors.append({
#                     "fa": f"دامنه «{domain.domain_name}»: تگ انتخاب شده («{tag.title}») هم‌اکنون برای شما فعال است و تغییری ایجاد نشد.",
#                     "en": f"Domain «{domain.domain_name}»: the selected tag («{tag.title}») is already active for you and no change was made."
#                 })
#                 continue
#
#             if not confirm:
#                 requires_confirm_list.append({
#                     "domain_name": domain.domain_name,
#                     "old_tag": existing_udt.tag.title,
#                     "new_tag": tag.title
#                 })
#             else:
#                 existing_udt.tag = tag
#                 existing_udt.updated_at = timezone.now()
#                 items_to_update.append(existing_udt)
#
#         if errors:
#             return Response({
#                 "error_code": 60,
#                 "message": {
#                     "fa": "خطا در ویرایش تگ‌ها.",
#                     "en": "Error in editing tags."
#                 },
#                 "detail": errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         if requires_confirm_list:
#             return Response({
#                 "error_code": 21,
#                 "message": {
#                     "fa": "ویرایش برخی تگ‌ها نیاز به تایید نهایی دارد.",
#                     "en": "Editing some tags requires final approval."
#                 },
#                 "detail": {
#                     "requires_confirmation": True,
#                     "conflicts": requires_confirm_list
#                 }
#             }, status=status.HTTP_409_CONFLICT)
#
#         with transaction.atomic():
#             if items_to_update:
#                 User_Domain_Tag.objects.bulk_update(items_to_update, fields=['tag', 'updated_at'])
#
#         return Response({
#             "message": {
#                 "fa": "ویرایش تگ‌ها با موفقیت انجام شد.",
#                 "en": "Tags were edited successfully."
#             }
#         }, status=status.HTTP_200_OK)
#
#     # =========================================================================
#     # 3. DELETE: delete the tags (Bulk Delete)
#     # =========================================================================
#     @swagger_auto_schema(
#         operation_description="Bulk soft deletion of user tags from domains using domain_name and title",        request_body=UserDomainTagSerializer(many=True),
#         responses={200: "tag deleted successfully ", 400: "Bad Request"}
#     )
#     def delete(self, request):
#         has_access, response = self._check_user_access(request.user)
#         if not has_access:
#             return response
#
#         user = request.user
#
#         items = request.data if isinstance(request.data, list) else [request.data]
#         ids_to_delete = set()
#         errors = []
#
#         for index, item in enumerate(items):
#             domain_name = item.get("domain_name")
#             title = item.get("title")
#
#             domain, err = self._get_domain_by_name(domain_name, index)
#             if err:
#                 errors.append(err)
#                 continue
#
#             existing_udts = User_Domain_Tag.objects.filter(
#                 user=user,
#                 domain=domain,
#                 deleted_at__isnull=True
#             )
#
#             if not existing_udts.exists():
#                 errors.append({
#                     "fa": f"دامنه «{domain.domain_name}»: تگ فعالی متعلق به شما برای حذف یافت نشد.",
#                     "en": f"Domain «{domain.domain_name}»: no active tag belonging to you was found to delete."
#                 })
#                 continue
#
#             if title:
#                 tag, err = self._get_tag_by_title(title, index)
#                 if err:
#                     errors.append(err)
#                     continue
#
#                 udts = existing_udts.filter(tag=tag)
#                 if not udts.exists():
#                     errors.append({
#                         "fa": f"دامنه «{domain.domain_name}»: تگ «{title}» توسط شما روی این دامنه ثبت نشده است.",
#                         "en": f"Domain «{domain.domain_name}»: tag «{title}» has not been registered by you on this domain."
#                     })
#                     continue
#
#                 ids_to_delete.extend(udts.values_list('id', flat=True))
#             else:
#                 ids_to_delete.extend(existing_udts.values_list('id', flat=True))
#
#         if errors:
#             return Response({
#                 "error_code": 60,
#                 "message": {
#                     "fa": "خطا در حذف تگ‌ها.",
#                     "en": "Error in deleting tags."
#                 },
#                 "detail": errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         with transaction.atomic():
#             if ids_to_delete:
#                 User_Domain_Tag.objects.filter(id__in=ids_to_delete).update(deleted_at=timezone.now())
#
#         return Response({
#             "message": {
#                 "fa": "تگ‌های انتخابی با موفقیت حذف شدند.",
#                 "en": "Selected tags were deleted successfully."
#             }
#         }, status=status.HTTP_200_OK)
