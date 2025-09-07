# shared/utils/logger.py
import json
import logging
import os
import sys
import inspect
import traceback
from typing import Any


class JsonFormatter(logging.Formatter):
    """JSON formatter for production/container environments"""
    
    RESERVED_ATTRS = {
        'name', 'msg', 'args', 'created', 'msecs', 'levelname', 'levelno',
        'pathname', 'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
        'lineno', 'funcName', 'processName', 'process', 'threadName', 'thread',
        'getMessage', 'message', 'asctime', 'relativeCreated', 'taskName'
    }
    
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

        # Extract extras correctly
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith('_'):
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
        if not logging.root.handlers:
            handler = logging.StreamHandler(sys.stdout)
            
            # Simple env check for JSON vs readable format
            use_json = os.getenv('JSON_LOGS', 'false').lower() == 'true'
            
            if use_json:
                formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
            else:
                # Use Python's standard formatter for local development
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)-8s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s',
                    datefmt='%H:%M:%S'
                )
            
            handler.setFormatter(formatter)
            logging.root.addHandler(handler)
            logging.root.setLevel(logging.INFO)

    def set_request_context(self, **kwargs):
        """Set request-scoped context"""
        self._request_context.update(kwargs)

    def clear_request_context(self):
        """Clear request context"""
        self._request_context = {}

    def _add_context(self, extra: dict | None) -> dict:
        """Add request context to extra fields"""
        combined = self._request_context.copy()
        if extra:
            combined.update(extra)
        return combined if combined else None

    def _log(self, level: int, msg: str, *args, **kwargs):
        """Internal log method that properly sets caller info"""
        extra = self._add_context(kwargs.pop("extra", None))
        exc_info = kwargs.pop("exc_info", None)
        
        # If exc_info is True, capture the current exception
        if exc_info is True:
            exc_info = sys.exc_info()
        
        # Get actual caller info
        frame = inspect.currentframe()
        # Skip 2 frames: _log and the wrapper method (info, error, etc.)
        if frame:
            frame = frame.f_back.f_back
            if frame:
                # Create record with proper caller info
                record = self.logger.makeRecord(
                    self.logger.name,
                    level,
                    frame.f_code.co_filename,
                    frame.f_lineno,
                    msg,
                    args,
                    exc_info,  # Pass the actual exception tuple, not True
                    func=frame.f_code.co_name,
                    extra=extra,
                    **kwargs
                )
                # Set module name properly
                module_name = frame.f_globals.get('__name__', '')
                if module_name:
                    record.module = module_name.split('.')[-1]
                
                self.logger.handle(record)
                return
        
        # Fallback if we can't get frame info
        self.logger.log(level, msg, *args, extra=extra, exc_info=exc_info, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        """Log an exception with full traceback"""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, msg, *args, **kwargs)


def create_logger(service_name: str) -> ServiceLogger:
    return ServiceLogger(service_name)