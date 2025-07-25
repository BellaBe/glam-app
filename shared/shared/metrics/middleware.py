# -------------------------------
# shared/metrics/middleware.py
# -------------------------------

"""
Prometheus metrics middleware for all services.

Provides standard HTTP metrics and allows services to register
their own domain-specific metrics.
"""

import time
import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Standard HTTP metrics for all services
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


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics collection middleware."""
    
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Get method and normalize path
        method = request.method
        path = self._normalize_path(request.url.path)
        
        # Track in-progress requests
        http_requests_in_progress.labels(service=self.service_name).inc()
        
        # Time the request
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record success metrics
            self._record_metrics(method, path, status_code, start_time)
            
            return response
            
        except Exception as e:
            # Record failure metrics
            self._record_metrics(method, path, 500, start_time)
            raise
        finally:
            http_requests_in_progress.labels(service=self.service_name).dec()
    
    def _record_metrics(self, method: str, path: str, status: int, start_time: float):
        """Record HTTP metrics."""
        http_requests_total.labels(
            service=self.service_name,
            method=method,
            endpoint=path,
            status=status
        ).inc()
        
        http_request_duration_seconds.labels(
            service=self.service_name,
            method=method,
            endpoint=path
        ).observe(time.time() - start_time)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize paths to prevent high cardinality."""
        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{id}',
            path
        )
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        return path


async def metrics_endpoint(request: Request) -> Response:
    """Endpoint to expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

