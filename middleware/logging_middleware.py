import logging
import json
import time
from django.utils.deprecation import MiddlewareMixin
import traceback
import sys

logger = logging.getLogger('myapp.requests')


class RequestLogMiddleware(MiddlewareMixin):
    """لاگ تمام درخواست‌ها و پاسخ‌ها"""

    def process_request(self, request):
        """قبل از پردازش درخواست"""
        request.start_time = time.time()

        # اطلاعات درخواست
        log_data = {
            'method': request.method,
            'path': request.path,
            'full_path': request.get_full_path(),
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }

        # برای متدهای POST/PUT، بدنه درخواست رو لاگ کن (به جز اطلاعات حساس)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.body:
            try:
                body = json.loads(request.body)
                # پاک کردن اطلاعات حساس
                sensitive_fields = ['password', 'token', 'key', 'secret', 'credit_card']
                for field in sensitive_fields:
                    if field in body:
                        body[field] = '******'
                log_data['body'] = body
            except:
                pass

        # ========== رفع مشکل Unicode ==========
        # لاگ بدون ایموجی و با encoding صحیح
        log_message = json.dumps(log_data, ensure_ascii=False)
        # جایگزینی ایموجی‌ها با متن ساده
        log_message = log_message.replace('📥', '[REQUEST]')
        log_message = log_message.replace('📤', '[RESPONSE]')

        # لاگ با encode به utf-8 برای جلوگیری از خطا
        try:
            logger.info(f"Request: {log_message}")
        except UnicodeEncodeError:
            # اگر باز هم خطا داد، با ascii لاگ کن
            logger.info(f"Request: {json.dumps(log_data, ensure_ascii=True)}")

        return None

    def process_response(self, request, response):
        """بعد از پردازش درخواست"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            log_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration': f"{duration:.3f}s",
                'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            }

            log_message = json.dumps(log_data, ensure_ascii=False)

            # لاگ خطاهای خاص
            if response.status_code >= 400:
                try:
                    logger.warning(f"Response Error: {log_message}")
                except UnicodeEncodeError:
                    logger.warning(f"Response Error: {json.dumps(log_data, ensure_ascii=True)}")
            else:
                try:
                    logger.info(f"Response: {log_message}")
                except UnicodeEncodeError:
                    logger.info(f"Response: {json.dumps(log_data, ensure_ascii=True)}")

        return response

    def process_exception(self, request, exception):
        """وقتی خطا رخ میده"""
        log_data = {
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            'exception': str(exception),
            'traceback': traceback.format_exc(),
        }

        log_message = json.dumps(log_data, ensure_ascii=False)
        try:
            logger.error(f"Exception: {log_message}")
        except UnicodeEncodeError:
            logger.error(f"Exception: {json.dumps(log_data, ensure_ascii=True)}")

        return None

    def get_client_ip(self, request):
        """دریافت IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip