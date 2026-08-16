# from django.contrib.auth import get_user_model
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.views import APIView
#
# from identity.serializers.reset_pass_serializer import PasswordResetWithBackupCodeSerializer
# from identity.utils import  verify_and_use_backup_code
#
# from drf_yasg.utils import swagger_auto_schema
# from django.db import transaction
#
# import json
# import logging
# import  django.utils.timezone as timezone
#
# logger = logging.getLogger('myapp')
# User = get_user_model()
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
# #Password Reset With Backup Code
# class PasswordResetWithBackupCodeView(APIView):
#     @swagger_auto_schema(
#         operation_description="""
#     Reset the user's password using a one-time backup code.
#
#     Security notes:
#     - The backup code is single-use and is invalidated after successful verification.
#     - Invalid account information and invalid backup codes return the same generic error
#       response to prevent user enumeration.
#     - Password values and backup codes are never included in security logs.
#
#     Custom error codes:
#     - code 10: Invalid input data or password format.
#     - code 75: Invalid account information or backup code.
#     """,
#         request_body=PasswordResetWithBackupCodeSerializer,
#         responses={
#             200: "Password reset successfully.",
#             400: "Invalid input data or backup code.",
#         }
#     )
#     def post(self, request):
#         serializer = PasswordResetWithBackupCodeSerializer(data=request.data)
#         if not serializer.is_valid():
#             log_critical_event(
#                     action='reset_password',
#                     status_type='failed',
#                     request=request,
#                     error_code=10,
#
#                 )
#             return Response({
#                 "error_code": 10,
#                 "message": {
#                     "fa": "اطلاعات ارسالی یا فرمت رمز عبور معتبر نیست.",
#                     "en": "The provided data or password format is invalid."
#                 },
#                 "detail": serializer.errors,
#             },status=status.HTTP_400_BAD_REQUEST)
#         username = serializer.validated_data['username'].lower()
#         backup_code = serializer.validated_data['backup_code']
#         new_password = serializer.validated_data['new_password']
#
#         try:
#             user = User.objects.get(username=username)
#
#             if user.status != 'active':
#                 log_critical_event(
#                     action='reset_password',
#                     status_type='failed',
#                     request=request,
#                     user_id=user.id,
#                     error_code=75,
#                     extra={
#                         'username': user.username,
#                         'account_status': user.status
#                     }
#                 )
#                 return Response({
#                     "error_code": 75,
#                     "message": {
#                         "fa": "اطلاعات وارد شده یا کد پشتیبان معتبر نیست.",
#                         "en": "The provided information or backup code is invalid."
#                     },
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#         except User.DoesNotExist:
#
#             log_critical_event(
#                 action='reset_password',
#                 status_type='failed',
#                 request=request,
#                 error_code=75,
#             )
#             return Response({
#                 "error_code": 75,
#                 "message": {
#                     "fa": "اطلاعات وارد شده یا کد پشتیبان معتبر نیست.",
#                     "en": "The provided information or backup code is invalid."
#                 },
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         with transaction.atomic():
#             result = verify_and_use_backup_code(user, backup_code)
#
#             if not result:
#                 log_critical_event(
#                     action='reset_password',
#                     status_type='failed',
#                     request=request,
#                     user_id=user.id,
#                     error_code=75,
#                     extra={
#                         'username': user.username,
#                     }
#                 )
#
#                 return Response({
#                     "error_code": 75,
#                     "message": {
#                         "fa": "اطلاعات وارد شده یا کد پشتیبان معتبر نیست.",
#                         "en": "The provided information or backup code is invalid."
#                     },
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#             user.set_password(new_password)
#             user.save(update_fields=['password'])
#
#         log_critical_event(
#             action="reset_password",
#             status_type='success',
#             request=request,
#             user_id=user.id,
#             extra={
#                 'username': user.username,
#             }
#         )
#
#         response_data = {
#             "message": {
#                 "fa": "رمز عبور شما با موفقیت تغییر یافت. می‌توانید وارد شوید.",
#                 "en": "Your password has been changed successfully. You can now log in."
#             },
#             "show_popup": True,
#             "new_backup_code": result,
#         }
#
#         return Response(response_data, status=status.HTTP_200_OK)