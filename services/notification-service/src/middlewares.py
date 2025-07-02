# File: services/notification-service/src/middlewares.py
from fastapi import FastAPI, Request, Response
from shared.api.middleware import setup_api_middleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import re
from .config import ServiceConfig

# Define Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['service', 'method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['service']
)

# Notification-specific metrics
notifications_sent_total = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['type', 'provider', 'status']
)

notifications_duration_seconds = Histogram(
    'notifications_duration_seconds',
    'Notification sending duration in seconds',
    ['type', 'provider']
)

email_queue_size = Gauge(
    'email_queue_size',
    'Current size of email queue'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Lightweight Prometheus middleware that works with shared middleware"""
    
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Get method and normalize path
        method = request.method
        path = self._normalize_path(request.url.path)
        
        # Track in-progress
        http_requests_in_progress.labels(service=self.service_name).inc()
        
        # Time the request
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            
            # Record metrics
            http_requests_total.labels(
                service=self.service_name,
                method=method,
                endpoint=path,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                service=self.service_name,
                method=method,
                endpoint=path
            ).observe(time.time() - start_time)
            
            return response
            
        except Exception as e:
            # Record failed request
            http_requests_total.labels(
                service=self.service_name,
                method=method,
                endpoint=path,
                status=500
            ).inc()
            
            http_request_duration_seconds.labels(
                service=self.service_name,
                method=method,
                endpoint=path
            ).observe(time.time() - start_time)
            
            raise
        finally:
            http_requests_in_progress.labels(service=self.service_name).dec()
    
    def _normalize_path(self, path: str) -> str:
        """Normalize paths to prevent high cardinality"""
        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{id}',
            path
        )
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        return path


async def metrics_endpoint(request: Request) -> StarletteResponse:
    """Endpoint to expose Prometheus metrics"""
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def add_middleware(app: FastAPI, config: ServiceConfig):
    """Add all middleware to app using shared components"""
    
    # Add Prometheus middleware FIRST (before shared middleware)
    # This ensures we capture all requests, even those that error
    app.add_middleware(
        PrometheusMiddleware,
        service_name=config.SERVICE_NAME
    )
    
    # Use shared API middleware for standardized responses and error handling
    setup_api_middleware(
        app,
        service_name=config.SERVICE_NAME,
        include_error_details=config.DEBUG
    )
    
    # Add metrics endpoint
    app.add_api_route(
        "/metrics",
        metrics_endpoint,
        methods=["GET"],
        include_in_schema=False,
        tags=["monitoring"]
    )


# Export metric functions for use in services
def increment_notification_sent(notification_type: str, provider: str, status: str):
    """Increment notification sent counter"""
    notifications_sent_total.labels(
        type=notification_type,
        provider=provider,
        status=status
    ).inc()


def observe_notification_duration(notification_type: str, provider: str, duration: float):
    """Record notification sending duration"""
    notifications_duration_seconds.labels(
        type=notification_type,
        provider=provider
    ).observe(duration)


def set_email_queue_size(size: int):
    """Update email queue size gauge"""
    email_queue_size.set(size)