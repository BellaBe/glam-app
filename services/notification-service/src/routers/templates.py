from fastapi import APIRouter, Depends, Query, status
from typing import  Optional, Annotated
from uuid import UUID
from shared.database import DBSessionDep
from shared.api import paginated_response, success_response, PaginationDep, RequestIdDep, CorrelationIdDep, Links
from ..services.template_service import TemplateService
from ..schemas.requests import TemplateCreate, TemplateUpdate, TemplatePreview, TemplateClone
from ..schemas.responses import (
    TemplateResponse, TemplatePreviewResponse, TemplateValidationResponse
)
from ..dependencies import get_template_service
from ..exceptions import TemplateNotFound

router = APIRouter(prefix="/notifications/templates", tags=["templates"])

@router.get("")
async def list_templates(
    pagination: PaginationDep,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep,
    type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    """List notification templates with pagination"""
    
    templates = await service.list_templates(
        session, type, is_active, pagination.offset, pagination.limit
    )
    
    # Get total count
    from ..repositories.template_repository import TemplateRepository
    repo = TemplateRepository(session)
    filters = {}
    if type:
        filters['type'] = type
    if is_active is not None:
        filters['is_active'] = is_active
    total = await repo.count(filters=filters)
    
    # Build response data
    data = [TemplateResponse.model_validate(t) for t in templates]
    
    # Build query params for links
    query_params = {}
    if type:
        query_params["type"] = type
    if is_active is not None:
        query_params["is_active"] = str(is_active).lower()
    
    return paginated_response(
        data=data,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        request_id=request_id,
        correlation_id=correlation_id,
        base_url="/api/v1/notifications/templates",
        **query_params
    )

@router.get("/{template_id}")
async def get_template(
    template_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """Get template details"""
    template = await service.get_template(template_id, session)
    
    if not template:
        raise TemplateNotFound(f"Template {template_id} not found")
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """Create new notification template"""
    template = await service.create_template(data, session, created_by="api")
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.put("/{template_id}")
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """Update existing template"""
    template = await service.update_template(template_id, data, session, updated_by="api")
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.delete("/{template_id}")
async def delete_template(
    template_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """Delete template (soft delete)"""
    await service.delete_template(template_id, session, deleted_by="api")
    
    return success_response(
        data={"message": "Template successfully deactivated"},
        request_id=request_id,
        correlation_id=correlation_id
    )

@router.post("/{template_id}/preview")
async def preview_template(
    template_id: UUID,
    data: TemplatePreview,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """Preview template with sample data"""
    preview = await service.preview_template(template_id, data.dynamic_content, session)
    
    return success_response(
        data=preview,
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.post("/{template_id}/validate")
async def validate_template(
    template_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """Validate template syntax and variables"""
    validation = await service.validate_template(template_id, session)
    
    return success_response(
        data=validation,
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.post("/{template_id}/clone", status_code=status.HTTP_201_CREATED)
async def clone_template(
    template_id: UUID,
    data: TemplateClone,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """Clone existing template"""
    template = await service.clone_template(template_id, data, session, created_by="api")
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )