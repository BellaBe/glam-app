from fastapi import APIRouter, Depends, Query, status, BackgroundTasks, Request
from typing import List, Optional, Annotated
from uuid import UUID
from shared.database import DBSessionDep
from shared.api import paginated_response, success_response, PaginationDep, RequestIdDep, CorrelationIdDep
from shared.api.correlation import CorrelationContext
from ..services.notification_service import NotificationService
from ..schemas.requests import NotificationCreate, BulkNotificationCreate
from ..schemas.responses import NotificationResponse, NotificationListResponse
from ..dependencies import get_notification_service
from ..exceptions import NotificationNotFound

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Resource: Notifications Collection
@router.get("", status_code=status.HTTP_200_OK, response_model=NotificationListResponse)
async def list_notifications(
    pagination: PaginationDep,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep,
    shop_id: Optional[UUID] = Query(None, description="Filter by shop ID"),
    status: Optional[str] = Query(None, description="Filter by status", enum=["pending", "sent", "failed"]),
    type: Optional[str] = Query(None, description="Filter by notification type"),
):
    """
    List notifications with filtering and pagination
    
    GET /notifications?shop_id=123&status=sent&page=1&limit=20
    """
    # Use correlation context for async operations
    async with CorrelationContext(correlation_id):
        notifications = await service.list_notifications(
            session, shop_id, status, type, pagination.offset, pagination.limit
        )
        
        total = await service.count_notifications(session, shop_id, status, type)
    
    # Build response data
    data = [NotificationResponse.model_validate(n) for n in notifications]
    
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

# Resource: Individual Notification
@router.get("/{notification_id}", status_code=status.HTTP_200_OK, response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep
):
    """
    Get a specific notification by ID
    
    GET /notifications/123e4567-e89b-12d3-a456-426614174000
    """
    async with CorrelationContext(correlation_id):
        notification = await service.get_notification(notification_id, session)
    
    if not notification:
        raise NotificationNotFound(f"Notification {notification_id} not found")
    
    return success_response(
        data=NotificationResponse.model_validate(notification),
        request_id=request_id,
        correlation_id=correlation_id,
    )

# Resource: Create Notification (Action endpoint)
@router.post("", status_code=status.HTTP_201_CREATED, response_model=NotificationResponse)
async def create_notification(
    payload: SendEmailRequest,
    svc: Annotated[NotificationService, Depends(get_notification_service)],
):

    # Use correlation context for async operations
    async with CorrelationContext(correlation_id):
        notification = await service.send_notification(data, session)
    
    return {"status": "queued"}

# Sub-resource: Notification Actions
@router.post("/{notification_id}/retry", status_code=status.HTTP_200_OK, response_model=NotificationResponse)
async def retry_notification(
    notification_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep,
):
    """
    Retry a failed notification
    
    POST /notifications/123.../retry
    """
    async with CorrelationContext(correlation_id):
        notification = await service.retry_notification(notification_id, session)
    
    return success_response(
        data=NotificationResponse.model_validate(notification),
        request_id=request_id,
        correlation_id=correlation_id,
    )

# Batch Operations (separate endpoint, not nested under notifications)
@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def create_batch_notifications(
    data: BulkNotificationCreate,
    background_tasks: BackgroundTasks,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep,
):
    """
    Create multiple notifications asynchronously
    
    POST /notifications/batch
    {
        "notification_type": "marketing",
        "recipients": [
            {"shop_id": "123...", "email": "user1@example.com"},
            {"shop_id": "456...", "email": "user2@example.com"}
        ]
    }
    
    Returns 202 Accepted with batch job ID
    """
    # Use correlation context
    async with CorrelationContext(correlation_id):
        # Create a batch job and process in background
        batch_id = await service.create_batch_job(data, session)
        
        # Process in background with correlation context
        async def process_with_correlation():
            async with CorrelationContext(correlation_id):
                await service.process_batch_notifications(
                    batch_id,
                    data,
                    session
                )
        
        background_tasks.add_task(process_with_correlation)
    
    return success_response(
        data={
            "batch_id": str(batch_id),
            "status": "processing",
            "notification_count": len(data.recipients),
            "notification_type": data.notification_type
        },
        request_id=request_id,
        correlation_id=correlation_id,
    )

# Batch Status
@router.get("/batch/{batch_id}")
async def get_batch_status(
    batch_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep
):
    """
    Get status of a batch notification job
    
    GET /notifications/batch/123...
    """
    async with CorrelationContext(correlation_id):
        batch_status = await service.get_batch_status(batch_id, session)
    
    if not batch_status:
        raise NotificationNotFound(f"Batch job {batch_id} not found")
    
    return success_response(
        data=batch_status,
        request_id=request_id,
        correlation_id=correlation_id,
    )

# Statistics/Analytics endpoint
@router.get("/statistics")
async def get_notification_statistics(
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: DBSessionDep,
    shop_id: Optional[UUID] = Query(None, description="Filter by shop ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
):
    """
    Get notification statistics
    
    GET /notifications/statistics?shop_id=123&start_date=2024-01-01
    """
    async with CorrelationContext(correlation_id):
        stats = await service.get_notification_statistics(
            session, shop_id, start_date, end_date
        )
    
    return success_response(
        data=stats,
        request_id=request_id,
        correlation_id=correlation_id,
    )