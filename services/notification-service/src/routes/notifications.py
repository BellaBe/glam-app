# services/notification-service/src/routes/notifications.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from src.dependencies import get_current_shop
from src.models.api import (
    NotificationResponse,
    SendEmailRequest,
    BulkEmailRequest,
)
from src.models.database import NotificationStatus, NotificationType
from src.utils.responses import create_response, create_paginated_response

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    request: Request,
    shop_id: Optional[UUID] = Query(None, description="Filter by shop ID (admin only)"),
    status: Optional[NotificationStatus] = Query(None, description="Filter by status"),
    type: Optional[NotificationType] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_shop: dict = Depends(get_current_shop),
):
    """List notifications with pagination"""
    # If not admin, force filter by current shop
    if not current_shop.get("is_admin") and shop_id != current_shop["id"]:
        shop_id = current_shop["id"]
    
    service = request.app.state.notification_service
    result = await service.list_notifications(
        shop_id=shop_id,
        status=status,
        notification_type=type,
        page=page,
        limit=limit,
    )
    
    return create_paginated_response(
        data=result["notifications"],
        page=page,
        limit=limit,
        total=result["total"],
        request_id=current_shop.get("request_id"),
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    request: Request,
    notification_id: UUID,
    current_shop: dict = Depends(get_current_shop),
):
    """Get notification details"""
    service = request.app.state.notification_service
    notification = await service.get_notification(notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Check permission
    if not current_shop.get("is_admin") and notification.shop_id != current_shop["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return create_response(
        data=notification,
        request_id=current_shop.get("request_id"),
    )


@router.post("/send")
async def send_notification(
    request: Request,
    body: SendEmailRequest,
    current_shop: dict = Depends(get_current_shop),
):
    """Manually send a notification (admin only)"""
    if not current_shop.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = request.app.state.notification_service
    result = await service.send_email(
        shop_id=body.shop_id,
        shop_domain=body.shop_domain,
        notification_type=body.type,
        to_email=body.to_email,
        subject=body.subject,
        template_variables=body.template_variables,
        metadata=body.metadata,
    )
    
    return create_response(
        data={
            "notification_id": str(result.id),
            "status": result.status,
            "message": "Notification sent successfully",
        },
        request_id=current_shop.get("request_id"),
    )


@router.post("/bulk")
async def send_bulk_notifications(
    request: Request,
    body: BulkEmailRequest,
    current_shop: dict = Depends(get_current_shop),
):
    """Send bulk notifications (admin only)"""
    if not current_shop.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = request.app.state.notification_service
    results = await service.send_bulk_emails(
        notification_type=body.type,
        recipients=body.recipients,
        subject=body.subject,
        metadata=body.metadata,
    )
    
    success_count = sum(1 for r in results if r.success)
    failed_count = len(results) - success_count
    
    return create_response(
        data={
            "total": len(results),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        },
        request_id=current_shop.get("request_id"),
    )


notifications_router = router