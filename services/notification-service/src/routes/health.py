from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text

from shared.database.dependencies import DBSessionDep
from src.utils.responses import create_response

router = APIRouter()


@router.get("/health")
async def health_check(db: DBSessionDep):
    """Health check endpoint"""
    try:
        # Check database connection
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        return create_response(
            data={
                "status": "healthy",
                "service": "notification-service",
            }
        )
    except Exception as e:
        return create_response(
            data={
                "status": "unhealthy",
                "service": "notification-service",
                "error": str(e),
            }
        )


health_router = router