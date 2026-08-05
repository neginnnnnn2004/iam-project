# identity/test_view.py
import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# ایجاد لاگر
logger = logging.getLogger('myapp')


class TestView(APIView):
    """ویو برای تست لاگ‌گیری"""

    def get(self, request):
        """درخواست GET"""

        # ========== لاگ‌های مختلف ==========
        logger.debug("🐛 این یه لاگ DEBUG هست! (برای دیباگ)")
        logger.info("✅ این یه لاگ INFO هست! (اطلاعات عمومی)")
        logger.warning("⚠️ این یه لاگ WARNING هست! (هشدار)")
        logger.error("❌ این یه لاگ ERROR هست! (خطا)")

        # ========== لاگ با اطلاعات درخواست ==========
        logger.info(f"📥 متد: {request.method}")
        logger.info(f"🌐 مسیر: {request.path}")
        logger.info(f"👤 کاربر: {request.user}")
        logger.info(f"📡 IP: {request.META.get('REMOTE_ADDR')}")
        logger.info(f"🔧 User-Agent: {request.META.get('HTTP_USER_AGENT')}")

        # ========== لاگ با context (اطلاعات اضافی) ==========
        log_data = {
            'user': str(request.user),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'timestamp': '2026-08-05 15:30:00'
        }
        logger.info(f"📊 اطلاعات کامل درخواست: {log_data}")

        # ========== لاگ برای تست خطا ==========
        try:
            # یه خطای تستی
            x = 1 / 0  # این خطا میده
        except Exception as e:
            logger.error(f"💥 خطای تستی رخ داد: {e}", exc_info=True)
            # exc_info=True یعنی stack trace رو هم لاگ کن

        # ========== پاسخ به کاربر ==========
        return Response({
            'message': 'سلام! لاگ‌ها با موفقیت ثبت شدن!',
            'status': 'success',
            'logs_sent': ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            'check_logs': 'به فایل‌های logs/app.log و logs/errors.log نگاه کن'
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """درخواست POST برای تست"""

        logger.info(f"📤 دریافت درخواست POST از {request.user}")
        logger.info(f"📦 داده‌های ارسالی: {request.data}")

        return Response({
            'message': 'POST درخواست دریافت شد!',
            'data': request.data
        }, status=status.HTTP_201_CREATED)