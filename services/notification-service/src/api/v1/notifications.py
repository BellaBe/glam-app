# services/notification-service/src/api/v1/notifications.py
from uuid import UUID

from fastapi import APIRouter, Query, Request

from shared.api import ApiResponse, paginated_response, success_response
from shared.api.dependencies import ClientAuthDep, PaginationDep, RequestContextDep
from shared.utils.exceptions import ForbiddenError

from ...dependencies import NotificationServiceDep
from ...schemas.notification import NotificationOut, NotificationStats

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("", response_model=ApiResponse[list[NotificationOut]], summary="List sent notifications")
async def list_notifications(
    svc: NotificationServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    pagination: PaginationDep,
    request: Request,
    status: str | None = Query(None, description="Filter by status"),
    merchant_id: UUID | None = Query(None, description="Filter by merchant"),
):
    """List notifications with optional filters"""
    # Permission check
    if auth.scope not in ["notifications:read", "notifications:write"]:
        raise ForbiddenError(message="Cannot read notifications", required_permission="notifications:read")

    # Get notifications
    total, notifications = await svc.list_notifications(
        skip=pagination.offset, limit=pagination.limit, status=status, merchant_id=merchant_id
    )

    # Return paginated response
    return paginated_response(
        data=notifications,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        base_url=str(request.url.path),
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )


@router.get("/stats", response_model=ApiResponse[NotificationStats], summary="Get notification statistics")
async def get_stats(svc: NotificationServiceDep, ctx: RequestContextDep, auth: ClientAuthDep):
    """Get daily notification statistics"""
    # Permission check
    if auth.scope not in ["notifications:read", "notifications:write"]:
        raise ForbiddenError(message="Cannot read notification stats", required_permission="notifications:read")

    stats = await svc.get_stats()

    return success_response(data=stats, request_id=ctx.request_id, correlation_id=ctx.correlation_id)


@router.get("/{notification_id}", response_model=ApiResponse[NotificationOut], summary="Get notification details")
async def get_notification(
    notification_id: UUID, svc: NotificationServiceDep, ctx: RequestContextDep, auth: ClientAuthDep
):
    """Get notification by ID"""
    # Permission check
    if auth.scope not in ["notifications:read", "notifications:write"]:
        raise ForbiddenError(message="Cannot read notifications", required_permission="notifications:read")

    # Get notification - service raises NotFoundError if missing
    notification = await svc.get_notification(notification_id)

    return success_response(data=notification, request_id=ctx.request_id, correlation_id=ctx.correlation_id)
