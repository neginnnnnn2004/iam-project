# import logging
# import json
# from django.utils import timezone
#
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
#
# from identity.models import User, Role
# from identity.permissions import IsAdminRole, IsSuperAdmin
# from identity.serializers.user_serializers import (
#     ListOfUsersSerializer,
#     UserRoleUpdateSerializer,
#     UserStatusUpdateSerializer,
#     ListOfRoleUsersSerializer
#
# )
#
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
#
# logger = logging.getLogger(__name__)
#
# # ================== Helper Functions =====================
# def get_client_meta(request):
#     """
#     Extracting network metadata for security logs
#     """
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0].strip()
#     else:
#         ip = request.META.get('REMOTE_ADDR', 'UNKNOWN')
#
#     user_agent = request.META.get('HTTP_USER_AGENT', 'UNKNOWN')
#     return {
#         'ip': ip,
#         'user_agent': user_agent
#     }
#
#
# def log_critical_event(action: str, status_type: str, request, user_id=None, error_code=None, extra=None):
#     """
#     Structured logging at critical and security-sensitive points in the system
#     """
#     client_info = get_client_meta(request)
#
#     log_data = {
#         'event_type': 'SECURITY_AUDIT',
#         'action': action,
#         'status': status_type,
#         'timestamp': timezone.now().isoformat(),
#         'client_ip': client_info['ip'],
#         'user_agent': client_info['user_agent'],
#     }
#
#     if user_id is not None:
#         log_data['user_id'] = user_id
#     if error_code:
#         log_data['error_code'] = error_code
#
#     if extra:
#         sensitive_keys = {
#             'password',
#             'confirm_password',
#             'old_password',
#             'new_password',
#             'token',
#             'access_token',
#             'refresh_token',
#             'authorization',
#             'backup_codes',
#         }
#         safe_extra = {k: v for k, v in extra.items() if k not in sensitive_keys}
#         log_data['extra'] = safe_extra
#
#     log_message = json.dumps(log_data, ensure_ascii=False)
#
#     if status_type in ['failed', 'error']:
#         logger.error(log_message)
#     elif status_type == 'success':
#         logger.info(log_message)
#     else:
#         logger.debug(log_message)
#
# # ================== 1. ListOfAllUsers =====================
# class ListOfUsersView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     @swagger_auto_schema(
#         operation_description="Get list of all users for admin",
#         responses={
#             200: ListOfUsersSerializer(many=True),
#             401: "Unauthorized",
#             403: "Forbidden",
#         }
#     )
#     def get(self, request):
#         try:
#             users = User.objects.all()
#             serializer = ListOfUsersSerializer(users, many=True)
#
#             log_critical_event(
#                 action='list_users',
#                 status_type='success',
#                 request=request,
#                 user_id=request.user.id,
#                 extra={
#                     'username': request.user.username,
#                     'count': users.count(),
#                 },
#             )
#             return Response(serializer.data, status=status.HTTP_200_OK)
#
#         except Exception:
#             log_critical_event(
#                 action='list_users',
#                 status_type='error',
#                 request=request,
#                 user_id=request.user.id,
#                 error_code='LIST_USERS_FAILED',
#             )
#             return Response(
#                 {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#
#
# # ================== 2. ListOfAllPendingUsers =====================
# class PendingUsersView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     @swagger_auto_schema(
#         operation_description="Get list of pending users for admin approval",
#         responses={
#             200: ListOfUsersSerializer(many=True),
#             401: "Unauthorized",
#             403: "Forbidden",
#         }
#     )
#     def get(self, request):
#         try:
#             users = User.objects.filter(status="pending")
#             serializer = ListOfUsersSerializer(users, many=True)
#             log_critical_event(
#                 action='list_pending_users',
#                 status_type='success',
#                 request=request,
#                 user_id=request.user.id,
#                 extra={
#                     'username': request.user.username,
#                     'count': users.count(),
#                 },
#             )
#
#             return Response(serializer.data, status=status.HTTP_200_OK)
#
#         except Exception:
#             log_critical_event(
#                 action='list_pending_users',
#                 status_type='error',
#                 request=request,
#                 user_id=request.user.id,
#                 error_code='LIST_PENDING_USERS_FAILED',
#             )
#
#             return Response(
#                 {
#                     "detail": "An error occurred while fetching pending users / خطایی در دریافت کاربران در انتظار رخ داده است."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#
# # ================== 3. ListOfAllRoles =====================
# class ListOfRolesView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminRole]
#
#     @swagger_auto_schema(
#         operation_description="Get list of all roles for admin",
#         responses={
#             200: ListOfRoleUsersSerializer(many=True),
#             401: "Unauthorized",
#             403: "Forbidden",
#         }
#     )
#     def get(self, request):
#         try:
#             roles = Role.objects.all()
#             serializer =     ListOfRoleUsersSerializer(roles, many=True)
#             log_critical_event(
#                 action='list_roles',
#                 status_type='success',
#                 request=request,
#                 user_id=request.user.id,
#                 extra={
#                     'username': request.user.username,
#                     'count': roles.count(),
#                 },
#             )
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception:
#             log_critical_event(
#                 action='list_roles',
#                 status_type='error',
#                 request=request,
#                 user_id=request.user.id,
#                 error_code='LIST_ROLES_FAILED',
#             )
#             return Response(
#                 {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#
# # ================== 4. AssignARoleToUsersBySuperAdmin =====================
# class AssignUserRoleView(APIView):
#     permission_classes = [IsAuthenticated, IsSuperAdmin]
#
#     @swagger_auto_schema(
#         operation_description="""
#         Assign or change a user's role (promote to admin, demote to regular user, or change guest to regular user) only by superadmin.
#
#         Custom Error Codes:
#         - Code 10: Invalid payload or parameters (e.g., self-role change attempt).
#         - Code 40: Target user not found or has been soft-deleted.
#         """,
#         request_body=UserRoleUpdateSerializer,
#         responses={
#             400: "Bad Request (Code 10)",
#             401: "Unauthorized",
#             403: "Forbidden",
#             404: "Not Found (Code 40)",
#             200: openapi.Response(
#                 description="Role assigned successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         "message": openapi.Schema(type=openapi.TYPE_STRING),
#                         "data": openapi.Schema(type=openapi.TYPE_OBJECT),
#                     }
#                 )
#             )
#         }
#     )
#     def patch(self, request, pk):
#         try:
#             target_user = User.objects.select_related('role').filter(pk=pk, deleted_at__isnull=True).first()
#
#             if not target_user:
#                 log_critical_event(
#                     action='change_user_role',
#                     status_type='error',
#                     request=request,
#                     user_id=request.user.id,
#                     error_code='USER_NOT_FOUND',
#                     extra={
#                         'target_user_id': pk,
#                     },
#                 )
#                 return Response({
#                     "error_code": 40,
#                     "messages": "User not found or deleted / کاربر مورد نظر یافت نشد یا ممکن است حذف شده باشد.",
#                     "detail": None
#                 }, status=status.HTTP_404_NOT_FOUND)
#
#             if target_user == request.user:
#                 log_critical_event(
#                     action='change_user_role',
#                     status_type='error',
#                     request=request,
#                     user_id=request.user.id,
#                     error_code='SELF_ROLE_CHANGE_ATTEMPT',
#                     extra={
#                         'target_user_id': pk,
#                     },
#                 )
#                 return Response({
#                     "error_code": 10,
#                     "messages": "You cannot change your own role / شما نمی‌توانید نقش خودتان را تغییر دهید.",
#                     "detail": None
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#             serializer = UserRoleUpdateSerializer(target_user, data=request.data, partial=True)
#             if not serializer.is_valid():
#                 log_critical_event(
#                     action='change_user_role',
#                     status_type='error',
#                     request=request,
#                     user_id=request.user.id,
#                     error_code='INVALID_ROLE_PAYLOAD',
#                     extra={
#                         'target_user_id': target_user.id,
#                     },
#                 )
#                 return Response({
#                     "error_code": 10,
#                     "messages": "Invalid payload for role assignment / اطلاعات ارسالی برای تغییر نقش معتبر نیست.",
#                     "detail": serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#             print("VALIDATED DATA:", serializer.validated_data)
#
#             old_role_id = target_user.role.id if target_user.role else None
#             old_role_title = target_user.role.title if target_user.role else "None"
#
#             updated_user = serializer.save()
#
#             print("UPDATED USER:", updated_user)
#             print("UPDATED ROLE:", updated_user.role)
#
#             new_role_id = updated_user.role.id if updated_user.role else None
#             new_role_title = updated_user.role.title if updated_user.role else "None"
#
#             log_critical_event(
#                 action='change_user_role',
#                 status_type='success',
#                 request=request,
#                 user_id=request.user.id,
#                 extra={
#                     'target_user_id': target_user.id,
#                     'old_role': {
#                         'id': old_role_id,
#                         'title': old_role_title,
#                     },
#                     'new_role': {
#                         'id': new_role_id,
#                         'title': new_role_title,
#                     },
#                 },
#             )
#
#             return Response({
#                 'message': "User role updated successfully / نقش کاربر با موفقیت بروزرسانی شد.",
#                 'data': serializer.data
#             }, status=status.HTTP_200_OK)
#
#         except Exception:
#             logger.exception(
#                 "ROLE_CHANGE_FAILED | TargetUser: %s | Admin: %s",
#                 pk,
#                 request.user.id,
#             )
#
#             log_critical_event(
#                 action='change_user_role',
#                 status_type='error',
#                 request=request,
#                 user_id=request.user.id,
#                 error_code='ROLE_CHANGE_FAILED',
#                 extra={
#                     'target_user_id': pk,
#                 },
#             )
#
#             return Response(
#                 {
#                     "detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
# # ================== 5.  ChangeTheUserStatus&SoftDeleteTheUsersBySuperAdmin =====================
# class ManageUsersStatusView(APIView):
#     permission_classes = [IsAuthenticated, IsSuperAdmin]
#
#     def get_object(self, pk):
#         return User.objects.filter(pk=pk, deleted_at__isnull=True).first()
#
#     @swagger_auto_schema(
#         operation_description="""
#         Manage and update user account status only by superadmin (e.g., approving pending users).
#
#         Valid Status Codes:
#         - pending: Awaiting approval
#         - active: Active / Approved
#         - suspended: Suspended
#         - unverified: Unverified
#
#         Custom Error Codes:
#         - Code 10: Invalid status value supplied in payload.
#         - Code 40: Target user not found or soft-deleted.
#         """,
#         request_body=UserStatusUpdateSerializer,
#         responses={
#             200: openapi.Response(
#                 description="User status updated successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         "message": openapi.Schema(type=openapi.TYPE_STRING),
#                         "data": openapi.Schema(type=openapi.TYPE_OBJECT),
#                     }
#                 )
#             ),
#             400: "Bad Request (Code 10)",
#             401: "Unauthorized",
#             403: "Forbidden",
#             404: "Not Found (Code 40)",
#         }
#     )
#     def patch(self, request, pk):
#         try:
#             user = self.get_object(pk)
#             if not user:
#                 log_critical_event(
#                     action="change_user_status",
#                     status_type="error",
#                     request=request,
#                     user_id=request.user.id,
#                     error_code="USER_NOT_FOUND",
#                     extra={
#                         'target_user_id': pk,
#                     }
#                 )
#                 return Response({
#                     "error_code": 40,
#                     "message": "User not found / کاربر مورد نظر یافت نشد.",
#                     "detail": None
#                 }, status=status.HTTP_404_NOT_FOUND)
#
#             serializer = UserStatusUpdateSerializer(user, data=request.data, partial=True)
#             if not serializer.is_valid():
#                 log_critical_event(
#                     action="change_user_status",
#                     status_type="error",
#                     request=request,
#                     user_id=request.user.id,
#                     error_code="INVALID_STATUS",
#                     extra={
#                         'target_user_id': pk,
#                         'requested_status': request.data.get('status'),
#                     }
#                 )
#                 return Response({
#                     "error_code": 10,
#                     "message": "Invalid status option selected / وضعیت انتخاب شده برای کاربر نامعتبر است.",
#                     "detail": serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#             old_status = user.status
#             updated_user = serializer.save()
#             new_status = updated_user.status
#
#             log_critical_event(
#                 action="change_user_status",
#                 status_type="success",
#                 request=request,
#                 user_id=request.user.id,
#                 extra={
#                     'target_user_id': user.id,
#                     'old_status': old_status,
#                     'new_status': new_status,
#                 }
#             )
#
#             return Response({
#                 "message": f"User status updated successfully to '{new_status}' / وضعیت کاربر با موفقیت به {new_status} تغییر یافت.",
#                 "data": serializer.data
#             }, status=status.HTTP_200_OK)
#
#         except Exception:
#             log_critical_event(
#                 action="change_user_status",
#                 status_type="error",
#                 request=request,
#                 user_id=request.user.id,
#                 error_code="STATUS_CHANGE_FAILED",
#                 extra={
#                     'target_user_id': pk,
#                 }
#             )
#             return Response(
#                 {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#
#     @swagger_auto_schema(
#         operation_description="""
#         Soft-delete a user account only by superadmin.
#
#         Custom Error Codes:
#         - Code 40: Target user not found or already deleted.
#         """,
#         responses={
#             204: "No Content",
#             401: "Unauthorized",
#             403: "Forbidden",
#             404: "Not Found (Code 40)",
#         }
#     )
#     def delete(self, request, pk):
#         try:
#             user = self.get_object(pk)
#
#             if not user:
#                 log_critical_event(
#                     action="soft_delete_user",
#                     status_type="error",
#                     request=request,
#                     user_id=request.user.id,
#                     error_code="USER_NOT_FOUND",
#                     extra={
#                         'target_user_id': pk,
#                     }
#                 )
#
#                 return Response({
#                     "error_code": 40,
#                     "message": "User not found or already deleted / کاربر مورد نظر یافت نشد یا از قبل حذف شده است.",
#                     "detail": None
#                 }, status=status.HTTP_404_NOT_FOUND)
#
#             user.deleted_at = timezone.now()
#             user.status = 'deleted'
#             user.save()
#
#             log_critical_event(
#                 action="soft_delete_user",
#                 status_type="success",
#                 request=request,
#                 user_id=request.user.id,
#                 extra={
#                     'target_user_id': user.id,
#                 }
#             )
#
#             return Response(status=status.HTTP_204_NO_CONTENT)
#
#         except Exception:
#             log_critical_event(
#                 action="soft_delete_user",
#                 status_type="error",
#                 request=request,
#                 user_id=request.user.id,
#                 error_code="SOFT_DELETE_FAILED",
#                 extra={
#                     'target_user_id': pk,
#                 }
#             )
#             return Response(
#                 {"detail": "An unexpected error occurred / خطای غیرمنتظره‌ای رخ داده است."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
