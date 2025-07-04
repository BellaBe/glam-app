from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional, Annotated
from uuid import UUID
from shared.database import DBSessionDep
from shared.api import paginated_response, success_response, PaginationDep, RequestIdDep, CorrelationIdDep
from ..services.template_service import TemplateService
from ..schemas.requests import TemplateCreate, TemplateUpdate
from ..schemas.responses import TemplateResponse
from ..dependencies import get_template_service
from ..exceptions import TemplateNotFoundError, TemplateAlreadyExistsError

router = APIRouter(prefix="/notifications/templates", tags=["templates"])

# Resource: Templates Collection
@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    pagination: PaginationDep,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep,
    type: Optional[str] = Query(None, description="Filter by notification type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    List notification templates with filtering and pagination
    
    GET /notifications/templates?type=order_confirmation&is_active=true
    """
    templates = await service.list_templates(
        session, type, is_active, pagination.offset, pagination.limit
    )
    
    total = await service.count_templates(session, type, is_active)
    
    data = [TemplateResponse.model_validate(t) for t in templates]
    
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

# Resource: Create Template
@router.post("", status_code=status.HTTP_201_CREATED, response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """
    Create a new notification template
    
    POST /notifications/templates
    {
        "name": "order_confirmation_v2",
        "type": "order_confirmation",
        "subject_template": "Order #{{ order_number }} Confirmed",
        "body_template": "<html>...</html>"
    }
    """
    # Check if template with same name and type exists
    existing = await service.get_template_by_name_and_type(data.name, data.type, session)
    if existing:
        raise TemplateAlreadyExistsError(
            f"Template '{data.name}' already exists for type '{data.type}'",
            template_id=str(existing.id)
        )
    
    template = await service.create_template(data, session)
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id
    )

# Resource: Individual Template
@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template_by_id(
    template_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """
    Get a specific template by ID
    
    GET /notifications/templates/123e4567-e89b-12d3-a456-426614174000
    """
    template = await service.get_template_by_id(template_id, session)
    
    if not template:
        raise TemplateNotFoundError(f"Template {template_id} not found")
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )

# Resource: Update Template
@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """
    Update an existing template
    
    PUT /notifications/templates/123...
    {
        "subject_template": "Updated subject",
        "body_template": "Updated body"
    }
    """
    template = await service.update_template(template_id, data, session)
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )

# Resource: Partial Update
@router.patch("/{template_id}", response_model=TemplateResponse)
async def patch_template(
    template_id: UUID,
    data: TemplateUpdate,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """
    Partially update a template
    
    PATCH /notifications/templates/123...
    {
        "is_active": false
    }
    """
    template = await service.update_template(template_id, data, session)
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )

# Resource: Delete Template
@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """
    Delete a template (soft delete)
    
    DELETE /notifications/templates/123...
    """
    await service.delete_template(template_id, session)
    
    # 204 No Content - no response body
    return None


# Action: Activate/Deactivate Template
@router.post("/{template_id}/activate", response_model=TemplateResponse)
async def activate_template(
    template_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """
    Activate a template
    
    POST /notifications/templates/123.../activate
    """
    template = await service.activate_template(template_id, session)
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )

@router.post("/{template_id}/deactivate", response_model=TemplateResponse)
async def deactivate_template(
    template_id: UUID,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """
    Deactivate a template
    
    POST /notifications/templates/123.../deactivate
    """
    template = await service.deactivate_template(template_id, session)
    
    return success_response(
        data=TemplateResponse.model_validate(template),
        request_id=request_id,
        correlation_id=correlation_id,
    )

# Action: Preview Template
@router.post("/{template_id}/preview")
async def preview_template(
    template_id: UUID,
    sample_data: dict,
    request_id: RequestIdDep,
    correlation_id: CorrelationIdDep,
    service: Annotated[TemplateService, Depends(get_template_service)],
    session: DBSessionDep
):
    """
    Preview a template with sample data
    
    POST /notifications/templates/123.../preview
    {
        "customer_name": "John Doe",
        "order_number": "12345"
    }
    """
    preview = await service.preview_template(template_id, sample_data, session)
    
    return success_response(
        data=preview,
        request_id=request_id,
        correlation_id=correlation_id,
    )