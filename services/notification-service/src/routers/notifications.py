from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from typing import List, Optional, Annotated
from uuid import UUID
from shared.database import DBSessionDep
from shared.api import paginated_response, success_response, PaginationDep, RequestIdDep, CorrelationIdDep
from ..services.notification_service import NotificationService
from ..schemas.requests import NotificationCreate, BulkNotificationCreate
from ..schemas.responses import NotificationResponse, NotificationDetailResponse
from ..dependencies import get_notification_service
from ..exceptions import NotificationNotFound

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
async def list_notifications(
    pagination: PaginationDep,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep,
    shop_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
):
    """List notifications with pagination"""
    
    notifications = await service.list_notifications(
        session, shop_id, status, type, pagination.offset, pagination.limit
    )
    
    total = await service.count_notifications(session, shop_id, status, type)
    
    # Build response data
    data = [NotificationResponse.from_orm(n) for n in notifications]
    
    # Build query params for links
    query_params = {}
    if shop_id:
        query_params["shop_id"] = str(shop_id)
    if status:
        query_params["status"] = status
    if type:
        query_params["type"] = type
    
    return paginated_response(
        data=data,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        request_id=request_id,
        correlation_id=correlation_id,
        base_url="/api/v1/notifications",
        **query_params
    )

@router.get("/{notification_id}")
async def get_notification(
    notification_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep
):
    """Get notification details"""
    notification = await service.get_notification(notification_id, session)
    
    if not notification:
        raise NotificationNotFound(f"Notification {notification_id} not found")
    
    return success_response(
        data=NotificationDetailResponse.from_orm(notification),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.post("/send", status_code=status.HTTP_201_CREATED)
async def send_notification(
    data: NotificationCreate,
    background_tasks: BackgroundTasks,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep
):
    """Send single notification (internal endpoint)"""
    notification = await service.send_notification(data, session)
    
    return success_response(
        data=NotificationResponse.from_orm(notification),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.post("/send-bulk")
async def send_bulk_notifications(
    data: BulkNotificationCreate,
    background_tasks: BackgroundTasks,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep
):
    """Send bulk notifications (internal endpoint)"""
    notifications = await service.send_bulk_notifications(data, session)
    
    return success_response(
        data=[NotificationResponse.from_orm(n) for n in notifications],
        request_id=request_id,
        correlation_id=correlation_id
    )