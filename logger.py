import logging
from datetime import datetime, timezone
from django.conf import settings


def get_logger(name='myapp'):
    return logging.getLogger(name)


api_logger = get_logger('api_logger')
task_logger = get_logger('task_logger')
db_logger = get_logger('db_logger')


def log_with_context(logger, level, message, **kwargs):
    context = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        **kwargs
    }

    log_func = getattr(logger, level.lower(), logger.info)

    log_func(message, extra={'extra': context})