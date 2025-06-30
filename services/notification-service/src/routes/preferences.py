# services/notification-service/src/routes/preferences.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from src.dependencies import get_current_shop
from src.models.api import NotificationPreferences, NotificationPreferencesUpdate
from src.utils.responses import create_response

router = APIRouter()


@router.get("/{shop_id}", response_model=NotificationPreferences)
async def get_preferences(
    request: Request,
    shop_id: UUID,
    current_shop: dict = Depends(get_current_shop),
):
    """Get shop notification preferences"""
    # Check permission
    if not current_shop.get("is_admin") and shop_id != current_shop["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    service = request.app.state.notification_service
    preferences = await service.get_preferences(shop_id)
    
    if not preferences:
        # Create default preferences
        preferences = await service.create_default_preferences(shop_id)
    
    return create_response(
        data=preferences,
        request_id=current_shop.get("request_id"),
    )


@router.put("/{shop_id}", response_model=NotificationPreferences)
async def update_preferences(
    request: Request,
    shop_id: UUID,
    body: NotificationPreferencesUpdate,
    current_shop: dict = Depends(get_current_shop),
):
    """Update shop notification preferences"""
    # Check permission
    if not current_shop.get("is_admin") and shop_id != current_shop["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    service = request.app.state.notification_service
    preferences = await service.update_preferences(
        shop_id=shop_id,
        updates=body,
    )
    
    return create_response(
        data=preferences,
        request_id=current_shop.get("request_id"),
    )


@router.post("/{shop_id}/unsubscribe/{token}")
async def unsubscribe(
    request: Request,
    shop_id: UUID,
    token: str,
):
    """Unsubscribe from all emails using token"""
    service = request.app.state.notification_service
    success = await service.unsubscribe_with_token(shop_id, token)
    
    if not success:
        raise HTTPException(status_code=404, detail="Invalid unsubscribe link")
    
    return create_response(
        data={"message": "Successfully unsubscribed from all email notifications"},
    )


preferences_router = router