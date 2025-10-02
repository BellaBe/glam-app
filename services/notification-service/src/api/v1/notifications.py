# services/notification-service/src/api/v1/notifications.py
from uuid import UUID

from fastapi import APIRouter, Query

from shared.api import ApiResponse, paginated_response_ctx, success_response
from shared.api.dependencies import ClientAuthDep, PaginationDep, RequestContextDep
from shared.utils.exceptions import ForbiddenError

from ...dependencies import NotificationServiceDep
from ...schemas.notification import NotificationOut, NotificationStats

notifications_router = APIRouter(prefix="/notifications")


@notifications_router.get("", response_model=ApiResponse[list[NotificationOut]], summary="List sent notifications")
async def list_notifications(
    svc: NotificationServiceDep,
    ctx: RequestContextDep,
    auth: ClientAuthDep,
    pagination: PaginationDep,
    status: str | None = Query(None, description="Filter by status"),
    merchant_id: UUID | None = Query(None, description="Filter by merchant"),
):
    if auth.scope not in ["notifications:read", "bff:api:access"]:
        raise ForbiddenError(message="Cannot read notifications", required_permission="notifications:read")

    filters = {}
    if status:
        filters["status"] = status
    if merchant_id:
        filters["merchant_id"] = str(merchant_id)

    total, notifications = await svc.list_notifications(
        skip=pagination.offset, limit=pagination.limit, filters=filters if filters else None
    )

    return paginated_response_ctx(
        data=notifications,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        ctx=ctx,
        # include filters so links preserve them
        status=status,
        merchant_id=str(merchant_id) if merchant_id else None,
    )


@notifications_router.get(
    "/stats", response_model=ApiResponse[NotificationStats], summary="Get notification statistics"
)
async def get_stats(svc: NotificationServiceDep, ctx: RequestContextDep, auth: ClientAuthDep):
    """Get daily notification statistics"""
    # Permission check
    if auth.scope not in ["notifications:read", "bff:api:access"]:
        raise ForbiddenError(message="Cannot read notification stats", required_permission="notifications:read")

    stats = await svc.get_stats()

    return success_response(data=stats, correlation_id=ctx.correlation_id)


@notifications_router.get(
    "/{notification_id}", response_model=ApiResponse[NotificationOut], summary="Get notification details"
)
async def get_notification(
    notification_id: UUID, svc: NotificationServiceDep, ctx: RequestContextDep, auth: ClientAuthDep
):
    """Get notification by ID"""
    # Permission check
    if auth.scope not in ["notifications:read", "bff:api:access"]:
        raise ForbiddenError(message="Cannot read notifications", required_permission="notifications:read")

    # Get notification - service raises NotFoundError if missing
    notification = await svc.get_notification(notification_id)

    return success_response(data=notification, correlation_id=ctx.correlation_id)
