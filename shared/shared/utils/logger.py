# shared/utils/logger.py
import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from contextvars import ContextVar


# Context variable for request-scoped data
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


class ServiceLogger:
    """
    Service-specific logger that automatically includes service name and request context.
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._setup_logging()
        self._logger = logging.getLogger(service_name)
    
    def _setup_logging(self):
        """Configure logging for this service"""
        env = os.getenv("APP_ENV", "dev").lower()
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Configure formatters based on environment
        if env == "prod":
            formatter = JsonFormatter(self.service_name)
        else:
            formatter = ConsoleFormatter(self.service_name)
        
        # Set up handlers
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        
        # Configure the service logger
        logger = logging.getLogger(self.service_name)
        logger.setLevel(log_level)
        logger.addHandler(console_handler)
        
        # Add file handler for production
        if env == "prod":
            file_handler = logging.handlers.RotatingFileHandler(
                f"logs/{self.service_name}.log",
                maxBytes=10485760,  # 10MB
                backupCount=5,
                encoding='utf8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    
    def set_request_context(self, **kwargs):
        """Set request-scoped context (e.g., request_id, user_id)"""
        ctx = request_context.get()
        ctx.update(kwargs)
        request_context.set(ctx)
    
    def clear_request_context(self):
        """Clear request context"""
        request_context.set({})
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        """Internal log method that adds context"""
        # Get request context
        ctx = request_context.get()
        
        # Add context to extra
        extra = kwargs.get('extra', {})
        extra.update(ctx)
        kwargs['extra'] = extra
        
        self._logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)


class ConsoleFormatter(logging.Formatter):
    """Console formatter that includes service name and request context"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__()
    
    def format(self, record):
        # Build context string from extra fields
        context_parts = []
        request_id = getattr(record, 'request_id', None)
        if request_id is not None:
            context_parts.append(f"request_id={request_id}")
        user_id = getattr(record, 'user_id', None)
        if user_id is not None:
            context_parts.append(f"user_id={user_id}")
        
        # Add any other extra fields
        for key in record.__dict__:
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'message', 'getMessage', 'request_id', 'user_id']:
                context_parts.append(f"{key}={getattr(record, key)}")
        
        # Format: 2024-01-15 10:30:45 - funding-service - INFO - [request_id=123] Processing order
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"{timestamp} - {self.service_name} - {record.levelname}"
        if context_parts:
            message += f" - [{' '.join(context_parts)}]"
        message += f" - {record.getMessage()}"
        
        if record.exc_info:
            message += '\n' + self.formatException(record.exc_info)
        
        return message


class JsonFormatter(logging.Formatter):
    """JSON formatter for production"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__()
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "message": record.getMessage(),
            "environment": os.getenv("APP_ENV", "dev"),
        }
        
        # Add request context from extra
        request_id = getattr(record, 'request_id', None)
        if request_id is not None:
            log_data['request_id'] = request_id
        user_id = getattr(record, 'user_id', None)
        if user_id is not None:
            log_data['user_id'] = user_id
        
        # Add any other extra fields
        for key in record.__dict__:
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'message', 'getMessage', 'request_id', 'user_id']:
                log_data[key] = getattr(record, key)
        
        # Add exception if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


# Factory function to create service logger
def create_logger(service_name: str) -> ServiceLogger:
    """
    Create a logger for a specific service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        ServiceLogger instance
    """
    return ServiceLogger(service_name)


# ============ USAGE ============

"""
USAGE:

1. In your service initialization (main.py or app.py):
```python
from shared.utils.logger import create_logger

# Create service-specific logger
logger = create_logger("funding-service")
```

2. Basic logging:
```python
logger.info("Service started")
logger.error("Connection failed", extra={"host": "localhost", "port": 5432})
```

3. In FastAPI middleware or request handler:
```python
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    # Set request context for all logs in this request
    logger.set_request_context(
        request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
        method=request.method,
        path=request.url.path
    )
    
    logger.info("Request started")
    response = await call_next(request)
    logger.info("Request completed", extra={"status_code": response.status_code})
    
    # Clear context after request
    logger.clear_request_context()
    return response
```

4. In any route or service method:
```python
@app.post("/api/orders")
async def create_order(order: Order, user_id: str = Depends(get_current_user)):
    # Add user context
    logger.set_request_context(user_id=user_id)
    
    logger.info("Creating order", extra={"order_id": order.id})
    # ... business logic ...
    logger.info("Order created successfully")
```

5. Output examples:

Development:
2024-01-15 10:30:45 - funding-service - INFO - [request_id=abc123 user_id=456] - Creating order

Production (JSON):
{"timestamp": "2024-01-15T10:30:45.123Z", "service": "funding-service", "level": "INFO", "message": "Creating order", "request_id": "abc123", "user_id": "456", "order_id": "789"}
"""