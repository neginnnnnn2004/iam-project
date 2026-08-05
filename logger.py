import logging
import json
from datetime import datetime
from django.conf import settings

def get_logger(name='myapp'):
    return logging.getLogger(name)
api_logger = get_logger(name='api_logger')
task_logger = get_logger(name='task_logger')
db_logger = get_logger(name='db_logger')

def log_with_context(logger, level,message, **kwargs):
    context = {
        'timestamp': datetime.now().isoformat(),
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        **kwargs
    }
    if level == 'info':
        logger.info(f"{message} | {json.dumps(context, ensure_ascii=False)}")
    elif level == 'error':
        logger.info(f"{message} | {json.dumps(context, ensure_ascii=False)}")
    elif level == 'warning':
        logger.info(f"{message} | {json.dumps(context, ensure_ascii=False)}")
    elif level == 'debug':
        logger.info(f"{message} | {json.dumps(context, ensure_ascii=False)}")
