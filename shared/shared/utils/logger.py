# shared/utils/logger.py
import logging
import sys
from typing import Any


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
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
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
