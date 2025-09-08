from datetime import UTC, datetime

from fastapi import APIRouter, Request

from shared.api.responses import success_response


def create_health_router(service_name: str, prefix: str = "") -> APIRouter:
    router = APIRouter(prefix=prefix)

    @router.get("/health", tags=["Health"])
    async def health_check(request: Request):
        """Basic health check endpoint with service name and timestamp"""
        return success_response(
            data={
                "status": "healthy",
                "service": service_name,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            correlation_id=getattr(request.state, "correlation_id", None),
        )

    return router
