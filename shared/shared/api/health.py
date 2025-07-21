# glam-app/shared/api/health.py

from fastapi import APIRouter, Request
from datetime import datetime, timezone
from shared.api.responses import success_response


def create_health_router(service_name: str) -> APIRouter:
    router = APIRouter()

    @router.get("/health", tags=["Health"])
    async def health_check(request: Request):
        """Basic health check endpoint with service name and timestamp"""
        return success_response(
            data={
                "status": "healthy",
                "service": service_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            request_id=getattr(request.state, "request_id", None),
            correlation_id=getattr(request.state, "correlation_id", None),
        )

    return router
