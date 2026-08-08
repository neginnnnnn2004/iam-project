from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from identity.serializers.reset_pass_serializer import PasswordResetWithBackupCodeSerializer
from identity.utils import  verify_and_use_backup_code

from drf_yasg.utils import swagger_auto_schema

import json
import logging

logger = logging.getLogger('myapp')
User = get_user_model()


# ================== help full def =====================
def get_client_ip(request):
    """دریافت IP واقعی کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def safe_json_dumps(data):
    """تبدیل به JSON با مدیریت خطا"""
    try:
        return json.dumps(data, ensure_ascii=False)
    except:
        return str(data)

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
        logger.info("=" * 60)
        logger.info(f'شروع فرآیند بازیابی رمز عبور')
        logger.info(f' IP: {get_client_ip(request)}')
        logger.info(f" User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}")
        logger.info(f"داده های درخواست: {safe_json_dumps(request.data)}")

        serializer = PasswordResetWithBackupCodeSerializer(data=request.data)
        if not serializer.is_valid():
            logger.info(f" اطلاعات ثبت نام نامعتبر است")
            logger.warning(f"خطاهای اعتبارسنجی: {safe_json_dumps(serializer.errors)}")
            logger.info("=" * 60)

            return Response({
                "error_code": 10,
                "message": "اطلاعات ارسالی یا فرمت رمز عبور معتبر نیست.",
                "detail": serializer.errors,
            },status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data['username'].lower()
        backup_code = serializer.validated_data['backup_code']
        new_password = serializer.validated_data['new_password']

        logger.info(f"نام کاربری برای بازیابی: {username}")
        logger.info(f"طول کد پشتیبان دریافت شده: {len(backup_code)} کاراکتر ")

        try:
            user = User.objects.get(username=username)
            logger.info(f" کاربر یافت شد: {user.username} (ID: {user.id})")
            logger.info(f" وضعیت فعلی کاربر: {user.status}")
            logger.info(f" ایمیل: {user.email}")
            logger.info(f" تلفن: {user.phone}")
            logger.info(f" نقش: {user.role.name if user.role else 'بدون نقش'}")

            if user.status != 'active':
                logger.warning(f" کاربر غیرفعال است! وضعیت فعلی: '{user.status}'")
                logger.warning(f"کاربر با نام {username} وجود دارد اما وضعیت '{user.status}' است")
                logger.info("=" * 60)
                return Response({
                    "error_code": 75,
                    "message": "اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"* کاربر فعال است و می‌تواند ریست پسورد کند")

        except User.DoesNotExist:
            logger.warning(f" کاربر با نام {username} یافت نشد")
            logger.info("=" * 60)
            return Response({
                "error_code": 75,
                "message": "اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"  شروع بررسی کد پشتیبان برای کاربر {user.username}")
        result = verify_and_use_backup_code(user, backup_code)

        if not result:
            logger.warning(f"کد پشتیبان نامعتبر برای کاربر {user.username}")
            logger.warning(f"تلاش ناموفق برای بازیابی رمز از IP {get_client_ip(request)}" )
            logger.info("=" * 60)
            return Response({
               "error_code": 75,
                "message":"اطلاعات وارد شده یا کد پشتیبان معتبر نیست."
            }, status=status.HTTP_400_BAD_REQUEST)
        logger.info(f" کد پشتیبان برای کاربر {user.username} معتبر است")

        logger.info(f" در حال تغییر رمز عبور برای کاربر {user.username}")
        user.set_password(new_password)
        user.save()

        logger.info(f" رمز عبور کاربر {user.username} با موفقیت تغییر کرد")
        response_data = {
            "message": "رمز عبور شما با موفقیت تغییر یافت. می‌توانید وارد شوید.",
            "show_popup": True,
            "new_backup_code": result ,
        }

        logger.info(f" فرآیند بازیابی رمز با موفقیت کامل شد")
        logger.info(f" کد پشتیبان جدید برای کاربر {user.username} صادر شد")
        logger.info("=" * 60)

        return Response(response_data, status=status.HTTP_200_OK)
