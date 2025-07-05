
# -------------------------------
# shared/metrics/__init__.py
# -------------------------------

"""Prometheus metrics utilities for microservices."""

from .middleware import (
    PrometheusMiddleware,
    metrics_endpoint,
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
)

__all__ = [
    "PrometheusMiddleware",
    "metrics_endpoint",
    "http_requests_total",
    "http_request_duration_seconds",
    "http_requests_in_progress",
]
