from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from uuid import UUID

from shared.api import (
    ApiResponse,
    success_response,
    paginated_response,
    Links,
    RequestContextDep,
    PaginationDep
)
from src.dependencies import NotificationServiceDep

from src.schemas import (
    NotificationResponse,
    NotificationListResponse,
    NotificationDetailResponse
)

router = APIRouter(tags=["notifications"])

@router.get(
    "",
    response_model=ApiResponse[NotificationListResponse],
    summary="List notification history"
)
async def list_notifications(
    svc: NotificationServiceDep,
    pagination: PaginationDep,
    ctx: RequestContextDep,
    shop_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
):
    """List notifications with pagination."""
    # Service returns tuple of (items, total)
    items, total = await svc.list_notifications(
        shop_id=shop_id,
        status=status,
        notification_type=type,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return paginated_response(
        data=items,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        base_url="/api/v1/notifications",
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        shop_id=shop_id,
        status=status,
        type=type
    )

@router.get(
    "/{notification_id}",
    response_model=ApiResponse[NotificationResponse],
    summary="Get notification details"
)
async def get_notification(
    notification_id: UUID,
    svc: NotificationServiceDep,
    ctx: RequestContextDep,
):
    """Get detailed notification information."""
    notification = await svc.get_notification(notification_id)
    
    if not notification:
        # The middleware will catch this and convert to standard error response
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return success_response(
        data=notification,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        links=Links(self=f"/api/v1/notifications/{notification_id}")
    )