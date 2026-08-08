import logging
import json
from datetime import datetime, timezone


class SafeJSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        extra_data = getattr(record, 'extra', None)
        if extra_data is not None:
            log_data["extra"] = extra_data

        try:
            return json.dumps(log_data, ensure_ascii=False, default=str)
        except Exception:
            log_data["message"] = str(record.getMessage())
            return json.dumps(log_data, ensure_ascii=False, default=str)