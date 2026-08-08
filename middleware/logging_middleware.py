import logging
import json
import time
import traceback

logger = logging.getLogger('myapp.requests')

SENSITIVE_KEYS = {'password', 'token', 'key', 'secret', 'credit_card', 'authorization'}


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        log_data = {
            'method': request.method,
            'path': request.path,
            'full_path': request.get_full_path(),
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }

        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            if 'multipart/form-data' not in content_type and request.body:
                try:
                    body = json.loads(request.body.decode('utf-8'))
                    log_data['body'] = self._sanitize_data(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    log_data['body'] = '[Non-JSON or Binary Data]'

        logger.info(f"Request: {request.method} {request.path}", extra={'extra': log_data})

        try:
            response = self.get_response(request)
        except Exception as exc:
            self._log_exception(request, exc)
            raise exc

        duration = time.time() - start_time
        response_log = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration': f"{duration:.3f}s",
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
        }

        if response.status_code >= 400:
            logger.warning(f"Response Error: {response.status_code} {request.path}", extra={'extra': response_log})
        else:
            logger.info(f"Response: {response.status_code} {request.path}", extra={'extra': response_log})

        return response

    def _sanitize_data(self, data):
        if isinstance(data, dict):
            clean_dict = {}
            for k, v in data.items():
                if k.lower() in SENSITIVE_KEYS:
                    clean_dict[k] = '******'
                else:
                    clean_dict[k] = self._sanitize_data(v)
            return clean_dict
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        return data

    def _log_exception(self, request, exception):
        exc_log = {
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'exception': str(exception),
            'traceback': traceback.format_exc(),
        }
        logger.error(f"Unhandled Exception: {request.path}", extra={'extra': exc_log})

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')