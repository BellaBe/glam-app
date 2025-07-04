from fastapi import APIRouter, Depends, status
from typing import Annotated
from uuid import UUID
from shared.database import DBSessionDep
from shared.api import success_response, RequestIdDep, CorrelationIdDep
from ..services.preference_service import PreferenceService
from ..schemas.requests import PreferenceCreate, PreferenceUpdate
from ..schemas.responses import PreferenceResponse
from ..dependencies import get_preference_service
from ..exceptions import PreferenceNotFound, PreferenceAlreadyExists

router = APIRouter(prefix="/notifications/preferences", tags=["preferences"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_preferences(
    data: PreferenceCreate,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[PreferenceService, Depends(get_preference_service)],
    session: DBSessionDep
):
    """Create notification preferences for a shop"""
    preferences = await service.create_preferences(data, session)
    
    return success_response(
        data=PreferenceResponse.model_validate(preferences),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.put("/{shop_id}")
async def update_preferences(
    shop_id: UUID,
    data: PreferenceUpdate,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[PreferenceService, Depends(get_preference_service)],
    session: DBSessionDep
):
    """Update notification preferences for a shop"""
    # Ensure shop_id in path matches the one in body
    if data.shop_id != shop_id:
        raise ValueError("Shop ID in path does not match shop ID in body")
    
    preferences = await service.update_preferences(data, session)
    
    return success_response(
        data=PreferenceResponse.model_validate(preferences),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.get("/{shop_id}")
async def get_preferences(
    shop_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[PreferenceService, Depends(get_preference_service)],
    session: DBSessionDep
):
    """Get notification preferences for a shop"""
    preferences = await service.get_preferences(shop_id, session)
    
    if not preferences:
        raise PreferenceNotFound(f"No preferences found for shop {shop_id}")
    
    return success_response(
        data=PreferenceResponse.model_validate(preferences),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.post("/unsubscribe")
async def unsubscribe(
    token: str,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[PreferenceService, Depends(get_preference_service)],
    session: DBSessionDep
):
    """Unsubscribe using token"""
    success = await service.unsubscribe_by_token(token, session)
    
    return success_response(
        data={"message": "Successfully unsubscribed from email notifications"},
        request_id=request_id,
        correlation_id=correlation_id
    )

@router.patch("/{shop_id}/notification-types/{notification_type}")
async def toggle_notification_type(
    shop_id: UUID,
    notification_type: str,
    enabled: bool,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[PreferenceService, Depends(get_preference_service)],
    session: DBSessionDep
):
    """Toggle specific notification type for a shop"""
    preferences = await service.toggle_notification_type(
        shop_id, notification_type, enabled, session
    )
    
    return success_response(
        data=PreferenceResponse.model_validate(preferences),
        request_id=request_id,
        correlation_id=correlation_id,
    )