# services/notification-service/src/routes/templates.py
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import EmailStr

from src.dependencies import get_current_shop
from src.models.api import NotificationTemplate, NotificationTemplateCreate, NotificationTemplateUpdate
from src.models.database import NotificationType
from src.utils.responses import create_response

router = APIRouter()


@router.get("/", response_model=List[NotificationTemplate])
async def list_templates(
    request: Request,
    is_active: bool = True,
    current_shop: dict = Depends(get_current_shop),
):
    """List available notification templates"""
    repo = request.app.state.template_repo
    templates = await repo.list_templates(is_active=is_active)
    
    return create_response(
        data=templates,
        request_id=current_shop.get("request_id"),
    )


@router.get("/{template_id}", response_model=NotificationTemplate)
async def get_template(
    request: Request,
    template_id: UUID,
    current_shop: dict = Depends(get_current_shop),
):
    """Get template details"""
    repo = request.app.state.template_repo
    template = await repo.get_by_id(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return create_response(
        data=template,
        request_id=current_shop.get("request_id"),
    )


@router.get("/type/{notification_type}", response_model=NotificationTemplate)
async def get_template_by_type(
    request: Request,
    notification_type: NotificationType,
    current_shop: dict = Depends(get_current_shop),
):
    """Get template by notification type"""
    repo = request.app.state.template_repo
    template = await repo.get_by_type(notification_type)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found for this type")
    
    return create_response(
        data=template,
        request_id=current_shop.get("request_id"),
    )


@router.post("/", response_model=NotificationTemplate)
async def create_template(
    request: Request,
    body: NotificationTemplate,
    current_shop: dict = Depends(get_current_shop),
):
    """Create a new template (admin only)"""
    if not current_shop.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    repo = request.app.state.template_repo
    
    # Check if template for this type already exists
    existing = await repo.get_by_type(body.type)
    if existing:
        raise HTTPException(status_code=409, detail="Template for this type already exists")
    
    template = await repo.create(body)
    
    return create_response(
        data=template,
        request_id=current_shop.get("request_id"),
    )


@router.put("/{template_id}", response_model=NotificationTemplate)
async def update_template(
    request: Request,
    template_id: UUID,
    body: NotificationTemplate,
    current_shop: dict = Depends(get_current_shop),
):
    """Update a template (admin only)"""
    if not current_shop.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    repo = request.app.state.template_repo
    template = await repo.update(template_id, body)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return create_response(
        data=template,
        request_id=current_shop.get("request_id"),
    )


templates_router = router