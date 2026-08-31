# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from django.utils import timezone
# from rest_framework.views import APIView
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
#
# from identity.models import Group, UserGroup, Domain
# from identity.permissions import IsAdminRole
# from identity.serializers.group_serializers import (
#     AdminListOfGroupsSerializer,
#     UserListOfGroupsSerializer,
#     UserGroupSerializer,
#     GroupSerializer,
#     GroupCreateSerializer,
#     GroupResponseSerializer
# )
# from identity.serializers.domain_serializers import DomainRegisterSerializer
#
#
# # 1. Group List
# class ListOfGroupsView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     @swagger_auto_schema(
#         operation_description="Retrieve the list of groups for any authenticated user. Regular users and guests see only the groups they belong to, while admins see all groups.",
#         responses={
#             200: UserListOfGroupsSerializer(many=True),
#             401: "Unauthorized",
#             403: "Forbidden",
#         }
#     )
#     def get(self, request):
#         user = request.user
#         is_admin = (
#                 user.is_superuser or
#                 (user.role is not None and user.role.code in ['admin', 'super_admin'])
#         )
#         active_groups = Group.objects.filter(deleted_at__isnull=True)
#
#         if is_admin:
#             groups = active_groups
#             serializer = AdminListOfGroupsSerializer(groups, many=True)
#         else:
#             user_group_ids = UserGroup.objects.filter(user=user).values_list('group_id', flat=True)
#             groups = active_groups.filter(id__in=user_group_ids).distinct()
#             serializer = UserListOfGroupsSerializer(groups, many=True)
#
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#
# # 2. Group Create
# class GroupRegisterView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     @swagger_auto_schema(
#         operation_description="""
#         Create a new group with admin access.
#
#         Custom error codes:
#
#         code 10: The submitted information is incomplete or incorrect.
#
#         """,
#         request_body=GroupCreateSerializer,
#         responses={
#             201: GroupResponseSerializer(),
#             400: "Bad Request (Code 10)",
#             401: "Unauthorized",
#             403: "Forbidden",
#         }
#     )
#     def post(self, request):
#         serializer = GroupCreateSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response({
#                 "error_code": 10,
#                 "message": {
#                     "fa": "اطلاعات ارسالی برای ایجاد گروه معتبر نیست.",
#                     "en": "The submitted information is not valid for creating a group."
#                 },
#                 "detail": serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         group = serializer.save()
#         return Response(GroupResponseSerializer(group).data, status=status.HTTP_201_CREATED)
#
#
# # 3. Group Detail, Update, Delete
# class GroupDetailOREditView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     def get_object(self, pk):
#         return Group.objects.select_related('assigned_by').filter(pk=pk, deleted_at__isnull=True).first()
#
#     @swagger_auto_schema(
#         operation_description="""
#         Retrieve the details of a group with admin access.
#
#         Custom error codes:
#
#         code 50: The requested group was not found.
#         """,
#         responses={
#             200: GroupSerializer(),
#             401: "Unauthorized",
#             403: "Forbidden",
#             404: "Not Found (Code 50)",
#         }
#     )
#     def get(self, request, pk):
#         group = self.get_object(pk)
#         if not group:
#             return Response({
#                 "error_code": 50,
#                 "message": {
#                     "fa": "گروه مورد نظر یافت نشد.",
#                     "en": "The requested group was not found."
#                 },
#                 "detail": None
#             }, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = GroupSerializer(group)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     @swagger_auto_schema(
#         operation_description="""
#         Edit Group with Admin Access
#
#         Specific Error Codes:
#         Code 10: The submitted information is invalid.
#         Code 50: The requested group was not found.
#
#         """,
#         request_body=GroupSerializer,
#         responses={
#             200: GroupSerializer(),
#             400: "Bad Request (Code 10)",
#             401: "Unauthorized",
#             403: "Forbidden",
#             404: "Not Found (Code 50)"
#         }
#     )
#     def patch(self, request, pk):
#         return self.update(request, pk, partial=True)
#
#     def update(self, request, pk, partial=False):
#         group = self.get_object(pk)
#         if not group:
#             return Response({
#                 "error_code": 50,
#                 "message": {
#                     "fa": "گروه مورد نظر جهت ویرایش یافت نشد.",
#                     "en": "The group to be edited was not found."
#                     },
#                 "detail": None
#             }, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = GroupSerializer(group, data=request.data, partial=partial)
#         if not serializer.is_valid():
#             return Response({
#                 "error_code": 10,
#                 "message": {
#                     "fa": "اطلاعات ارسالی برای ویرایش  گروه معتبر نیست.",
#                     "en": "The submitted information is not valid for editing a group."
#                 },
#                 "detail": serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     @swagger_auto_schema(
#         operation_description="""
#         Soft Delete Group with Admin Access
#
#         Specific Error Codes:
#
#         Code 50: The requested group was not found.
#         """,
#         responses={
#             204: "No Content",
#             401: "Unauthorized",
#             403: "Forbidden",
#             404: "Not Found (Code 50)",
#         }
#     )
#     def delete(self, request, pk):
#         group = self.get_object(pk)
#         if not group:
#             return Response({
#                 "error_code": 50,
#                 "message": {
#                     "fa": "گروه مورد نظر قبلاً حذف شده یا وجود ندارد.",
#                     "en": "The requested group has already been deleted or does not exist."
#                 },
#                 "detail": None
#             }, status=status.HTTP_404_NOT_FOUND)
#
#         group.deleted_at = timezone.now()
#         group.save()
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#
# # 4. Assign users to group by admin
# class AssignUsersGroups(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     @swagger_auto_schema(
#         operation_description="""
#         Assign Users to an Existing Group by Admin
#
#         Specific Error Codes:
#
#         Code 10: The submitted information (user ID or group ID) is incomplete or invalid.
#         """,
#         request_body=UserGroupSerializer,
#         responses={
#             400: "Bad Request (Code 10)",
#             401: "Unauthorized",
#             403: "Forbidden",
#             201: openapi.Response(
#                 description="Assigned successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         "message": openapi.Schema(type=openapi.TYPE_STRING),
#                         "data": openapi.Schema(type=openapi.TYPE_OBJECT)
#                     }
#                 )
#             )
#         }
#     )
#     def post(self, request):
#         serializer = UserGroupSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response({
#                 "error_code": 10,
#                 "message": {
#                     "fa": "اطلاعات ارسالی برای انتساب کاربر به گروه معتبر نیست.",
#                     "en": "The submitted information for assigning the user to the group is invalid."
#                 },
#                 "detail": serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         user_group = serializer.save(assigned_by=request.user)
#
#         return Response({
#             "message": {
#                 "fa": "کاربر با موفقیت به گروه انتساب داده شد.",
#                 "en": "The user was successfully assigned to the group."
#             },
#              "data": UserGroupSerializer(user_group).data
#         }, status=status.HTTP_201_CREATED)
#
#
# # 5. Group Domains List
# class GroupDomainView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     @swagger_auto_schema(
#         operation_description="""
#         Get List of Domains Associated with a Specific Group
#
#         Access Levels:
#
#         Admin and Superadmin: Access to domains of all groups
#
#         Regular User and Guest: Can only view domains of groups they are a member of
#
#         Error Codes:
#         65: The requested group does not exist or has been deleted
#          66: The user does not have access to this group
#
#          """,
#         manual_parameters=[
#             openapi.Parameter(
#                 'group_id',
#                 openapi.IN_PATH,
#                 description=" (ID) Group",
#                 type=openapi.TYPE_INTEGER,
#                 required=True,
#             )
#         ],
#         responses={
#             200: DomainRegisterSerializer(many=True),
#             401: "Unauthorized",
#             403: "Forbidden(Code 66)",
#             404: "Not Found (Code 65)",
#         }
#     )
#     def get(self, request, group_id):
#         group = Group.objects.filter(pk=group_id, deleted_at__isnull=True).first()
#         if not group:
#             return Response({
#                 "error_code": 65,
#                 "message": {
#                     "fa": "گروه مورد نظر یافت نشد.",
#                     "en": "The requested group was not found."
#                 },
#             }, status=status.HTTP_404_NOT_FOUND)
#
#         user = request.user
#         role_code = getattr(user.role, 'code',None)
#         is_admin = user.is_superuser or (role_code in ['admin','super_admin'])
#
#         if not is_admin:
#             is_assigned = UserGroup.objects.filter(user=user, group=group).exists()
#             if not is_assigned:
#                 return Response({
#                     "error_code": 66,
#                     "message": {
#                         "fa": "شما به این گروه دسترسی ندارید.",
#                         "en": "You do not have access to this group."
#                     },
#                 }, status=status.HTTP_403_FORBIDDEN)
#
#         domains = Domain.objects.filter(groups=group, deleted_at__isnull=True).distinct()
#         serializer = DomainRegisterSerializer(domains, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)