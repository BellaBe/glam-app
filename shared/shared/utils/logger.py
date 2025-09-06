# shared/utils/logger.py
import json
import logging
import sys
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra"):
            for key, value in record.extra.items():
                if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    log_record[key] = str(value)
                else:
                    log_record[key] = value

        return json.dumps(log_record)


class ServiceLogger:
    """Service logger that wraps Python's standard logger"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self._request_context: dict[str, Any] = {}

        # Only add handler if root logger has no handlers
        # This prevents duplicate handlers in reload
        if not logging.root.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
            handler.setFormatter(formatter)
            logging.root.addHandler(handler)
            logging.root.setLevel(logging.INFO)

    def set_request_context(self, **kwargs):
        """Set request-scoped context"""
        self._request_context = kwargs

    def clear_request_context(self):
        """Clear request context"""
        self._request_context = {}

    def _add_context(self, extra: dict | None) -> dict:
        """Add request context to extra fields"""
        combined = self._request_context.copy()
        if extra:
            combined.update(extra)
        return combined if combined else None

    def info(self, msg, *args, **kwargs):
        extra = kwargs.pop("extra", None)
        self.logger.info(msg, *args, extra=self._add_context(extra), **kwargs)

    def error(self, msg, *args, **kwargs):
        extra = kwargs.pop("extra", None)
        self.logger.error(msg, *args, extra=self._add_context(extra), **kwargs)

    def warning(self, msg, *args, **kwargs):
        extra = kwargs.pop("extra", None)
        self.logger.warning(msg, *args, extra=self._add_context(extra), **kwargs)

    def debug(self, msg, *args, **kwargs):
        extra = kwargs.pop("extra", None)
        self.logger.debug(msg, *args, extra=self._add_context(extra), **kwargs)

    def critical(self, msg, *args, **kwargs):
        extra = kwargs.pop("extra", None)
        self.logger.critical(msg, *args, extra=self._add_context(extra), **kwargs)


def create_logger(service_name: str) -> ServiceLogger:
    return ServiceLogger(service_name)
