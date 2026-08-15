import json
import logging
import django.utils.timezone as timezone

logger = logging.getLogger(__name__)

# ================== Helper Functions =====================
def get_client_meta(request):
    """
    Extracting network metadata for security logs
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'UNKNOWN')

    user_agent = request.META.get('HTTP_USER_AGENT', 'UNKNOWN')
    return {
        'ip': ip,
        'user_agent': user_agent
    }


def log_critical_event(action: str, status_type: str, request, user_id=None, error_code=None, extra=None):
    """
    Structured logging at critical and security-sensitive points in the system
    """
    client_info = get_client_meta(request)

    log_data = {
        'event_type': 'SECURITY_AUDIT',
        'action': action,
        'status': status_type,
        'timestamp': timezone.now().isoformat(),
        'client_ip': client_info['ip'],
        'user_agent': client_info['user_agent'],
    }

    if user_id is not None:
        log_data['user_id'] = user_id
    if error_code:
        log_data['error_code'] = error_code

    if extra:
        sensitive_keys = {
            'password',
            'confirm_password',
            'old_password',
            'new_password',
            'token',
            'access_token',
            'refresh_token',
            'authorization',
            'backup_codes',
        }
        safe_extra = {k: v for k, v in extra.items() if k not in sensitive_keys}
        log_data['extra'] = safe_extra

    log_message = json.dumps(log_data, ensure_ascii=False)

    if status_type in ['failed', 'error']:
        logger.error(log_message)
    elif status_type == 'success':
        logger.info(log_message)
    else:
        logger.debug(log_message)