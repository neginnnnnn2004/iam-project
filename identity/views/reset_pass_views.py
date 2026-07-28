from django.contrib.auth import get_user_model
from django.db.models.expressions import result
from rest_framework.response import Response
from rest_framework import status, response
from rest_framework.views import APIView

from identity.serializers.reset_pass_serializer import PasswordResetWithBackupCodeSerializer
from identity.utils import  verify_and_use_backup_code

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
User = get_user_model()

#Password Reset With Backup Code
class PasswordResetWithBackupCodeView(APIView):
    @swagger_auto_schema(
        operation_description="بازیابی و بازنشانی رمز عبور با استفاده از کدهای پشتیبان یک‌بار مصرف",
        request_body=PasswordResetWithBackupCodeSerializer,
        responses={
            200: "Password changed successfully",
            400: "Invalid input or code",
        }
    )
    def post(self, request):
        serializer = PasswordResetWithBackupCodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی یا فرمت رمز عبور معتبر نیست.",
                "detail": serializer.errors,
            },status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data['username'].lower()
        backup_code = serializer.validated_data['backup_code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(username=username, status='active')
        except User.DoesNotExist:
            return Response({
                "error_code": 75,
                "message": "اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
            },status=status.HTTP_400_BAD_REQUEST)

        result = verify_and_use_backup_code(user, backup_code)

        if not result:
            return Response({
               "error_code": 75,
                "message":"اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        response_data = {
            "message": "رمز عبور شما با موفقیت تغییر یافت. می‌توانید وارد شوید.",
            "show_popup": True,
            "new_backup_code": result ,
        }

        return Response(response_data, status=status.HTTP_200_OK)
