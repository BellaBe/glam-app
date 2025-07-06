# services/notification-service/src/api/templates.py
"""Template management endpoints"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from shared.api import (
    ApiResponse,
    success_response,
    Links,
    RequestContextDep
)
from src.dependencies import TemplateServiceDep

from src.schemas.template import (
    TemplateResponse,
    TemplateListResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    TemplateValidationRequest,
    TemplateValidationResponse
)

router = APIRouter(tags=["templates"])

@router.get(
    "",
    response_model=ApiResponse[TemplateListResponse],
    summary="List all available templates"
)
async def list_templates(
    svc: TemplateServiceDep,
    ctx: RequestContextDep,
    category: Optional[str] = Query(None, description="Filter by category (system, marketing, transactional)"),
):
    """
    List all available notification templates.
    
    Templates are defined in the system and include:
    - System templates (billing notifications)
    - Transactional templates (order, registration)
    - Marketing templates (custom campaigns)
    """
    # Get all template types
    template_types = svc.get_available_types()
    
    # Build template list with metadata
    templates = []
    for template_type in template_types:
        template = await svc.get_template_for_type(template_type)
        if template:
            # Determine category based on type
            template_category = _get_template_category(template_type)
            
            # Filter by category if specified
            if category and template_category != category:
                continue
            
            templates.append({
                'type': template_type,
                'name': template_type.replace('_', ' ').title(),
                'category': template_category,
                'variables': template['variables'],
                'preview_available': True
            })
    
    # Sort templates by category and name
    templates.sort(key=lambda x: (x['category'], x['name']))
    
    return success_response(
        data={
            'templates': templates,
            'total': len(templates)
        },
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        links=Links(self="/api/v1/templates")
    )

@router.get(
    "/{template_type}",
    response_model=ApiResponse[TemplateResponse],
    summary="Get template details by type"
)
async def get_template(
    template_type: str,
    svc: TemplateServiceDep,
    ctx: RequestContextDep,
    preview: bool = Query(False, description="Include preview with sample data")
):
    """
    Get detailed information about a specific template type.
    
    Optionally include a preview with sample data to see how the template renders.
    """
    template = await svc.get_template_for_type(template_type)
    
    if not template:
        raise HTTPException(
            status_code=404, 
            detail=f"Template not found: {template_type}"
        )
    
    response_data = {
        'type': template_type,
        'name': template_type.replace('_', ' ').title(),
        'category': _get_template_category(template_type),
        'subject_template': template['subject'],
        'body_template': template['body'],
        'variables': template['variables'],
        'global_variables': [
            'platform_name',
            'current_year',
            'support_url',
            'unsubscribe_url'
        ]
    }
    
    # Include preview if requested
    if preview:
        preview_result = await svc.preview_template(template_type)
        response_data['preview'] = preview_result
    
    return success_response(
        data=response_data,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        links=Links(
            self=f"/api/v1/templates/{template_type}",
            next=f"/api/v1/templates/{template_type}/preview"
        )
    )

@router.post(
    "/{template_type}/preview",
    response_model=ApiResponse[TemplatePreviewResponse],
    summary="Preview template with custom data"
)
async def preview_template(
    template_type: str,
    request: TemplatePreviewRequest,
    svc: TemplateServiceDep,
    ctx: RequestContextDep,
):
    """
    Preview a template with custom sample data.
    
    Useful for testing templates with specific variable values
    before sending actual notifications.
    """
    template = await svc.get_template_for_type(template_type)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_type}"
        )
    
    # Preview with provided data
    preview_result = await svc.preview_template(
        template_type,
        request.sample_data
    )
    
    if 'error' in preview_result:
        raise HTTPException(
            status_code=400,
            detail=preview_result['error']
        )
    
    return success_response(
        data=preview_result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        links=Links(
            self=f"/api/v1/templates/{template_type}/preview",
            previous=f"/api/v1/templates/{template_type}"
        )
    )

@router.post(
    "/validate",
    response_model=ApiResponse[TemplateValidationResponse],
    summary="Validate template syntax"
)
async def validate_template(
    request: TemplateValidationRequest,
    svc: TemplateServiceDep,
    ctx: RequestContextDep,
):
    """
    Validate Jinja2 template syntax.
    
    Useful for validating custom templates before saving them.
    """
    validation_result = svc.validate_template_syntax(
        request.subject,
        request.body
    )
    
    return success_response(
        data=validation_result,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
        links=Links(self="/api/v1/templates/validate")
    )

def _get_template_category(template_type: str) -> str:
    """Determine template category based on type"""
    if template_type.startswith('billing_'):
        return 'system'
    elif template_type in ['welcome', 'sync_start', 'sync_completed']:
        return 'transactional'
    else:
        return 'marketing'