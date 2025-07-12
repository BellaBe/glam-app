# services/credit-service/src/api/v1/health.py
"""Health check endpoints."""

from fastapi import APIRouter
from shared.api.health import create_health_router

from ...dependencies import LifecycleDep

router = APIRouter()

# Add the standard health endpoints
health_router = create_health_router()
router.include_router(health_router)


@router.get("/health/detailed")
async def detailed_health_check(lifecycle: LifecycleDep):
    """Detailed health check with component status"""

    health_status = {
        "status": "healthy",
        "components": {
            "database": "healthy",
            "redis": "healthy",
            "messaging": "healthy",
        },
        "metrics": {
            "total_accounts": 0,
            "total_transactions": 0,
            "zero_balance_accounts": 0,
        },
    }

    try:
        # Check database
        if lifecycle.db_manager:
            async with lifecycle.db_manager.get_session() as session:
                result = await session.execute("SELECT 1")
                if not result.scalar():
                    health_status["components"]["database"] = "unhealthy"
                    health_status["status"] = "degraded"

        # Check Redis
        if lifecycle.redis_client:
            await lifecycle.redis_client.ping()
        else:
            health_status["components"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"

        # Check messaging
        if (
            not lifecycle.messaging_wrapper
            or not lifecycle.messaging_wrapper.is_connected()
        ):
            health_status["components"]["messaging"] = "unhealthy"
            health_status["status"] = "degraded"

        # Get some basic metrics
        if lifecycle.credit_repo:
            zero_balance_merchants = (
                await lifecycle.credit_repo.get_merchants_with_zero_balance()
            )
            health_status["metrics"]["zero_balance_accounts"] = len(
                zero_balance_merchants
            )

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)

    return health_status
