from django.contrib.auth import authenticate, get_user_model
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from identity.utils import  verify_and_use_backup_code

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
User = get_user_model()

#Password Reset With Backup Code
class PasswordResetWithBackupCodeView(APIView):
    @swagger_auto_schema(
        operation_description="بازیابی و بازنشانی رمز عبور با استفاده از کدهای پشتیبان یک‌بار مصرف",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'backup_code', 'new_password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'backup_code': openapi.Schema(type=openapi.TYPE_STRING),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: "Password changed successfully",
            400: "Invalid input or code",
        }
    )
    def post(self, request):
        username = request.data.get("username")
        backup_code = request.data.get("backup_code") or request.data.get("backup_codes")
        new_password = request.data.get("new_password")

        if not username or not backup_code or not new_password:
            return Response({
                "error_code": 10,
                "message": "نام کاربری، کد پشتیبان و رمز عبور جدید الزامی هستند."
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=username.lower(), status='active')
        except User.DoesNotExist:
            return Response({
                "error_code": 75,
                "message": "اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
            }, status=status.HTTP_400_BAD_REQUEST)

        is_valid = verify_and_use_backup_code(user, backup_code)

        if not is_valid:
            return Response({
                "error_code": 75,
                "message": "اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({
            "message": "رمز عبور شما با موفقیت تغییر یافت."
        }, status=status.HTTP_200_OK)