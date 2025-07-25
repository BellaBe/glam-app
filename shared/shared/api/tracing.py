# shared/api/tracing.py
from typing import Optional
from fastapi import Request
from contextvars import ContextVar
from uuid7 import uuid7
from starlette.middleware.base import BaseHTTPMiddleware
from .correlation import set_correlation_context

_trace_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
                                

def set_trace_context(trace_id: Optional[str]) -> None:
    _trace_ctx.set(trace_id)

def get_trace_context() -> Optional[str]:
    return _trace_ctx.get()

class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle trace_id and correlation_id for all requests"""
    
    async def dispatch(self, request: Request, call_next):
        # 🆕 Extract or generate trace_id from W3C traceparent
        trace_id = self._extract_trace_id(request) or str(uuid7())
        
        # Extract or generate correlation_id
        correlation_id = request.headers.get("x-correlation-id") or trace_id
        
        # Set context for this request
        set_trace_context(trace_id)
        set_correlation_context(correlation_id)
        
        # Add to request state
        request.state.trace_id = trace_id
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add headers to response
        response.headers["x-trace-id"] = trace_id
        response.headers["x-correlation-id"] = correlation_id
        
        return response
    
    def _extract_trace_id(self, request: Request) -> Optional[str]:
        """Extract trace ID from W3C traceparent header"""
        traceparent = request.headers.get("traceparent")
        if traceparent:
            # W3C traceparent format: version-trace_id-parent_id-flags
            parts = traceparent.split("-")
            if len(parts) >= 2:
                return parts[1]  # Return trace_id part
        return None



