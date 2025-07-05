# services/notification-service/src/schemas/template.py
"""Template-related request/response schemas"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class TemplateRequest(BaseModel):
    """Requestbody for getting template"""
    type: str = Field(..., description="Type of the template to retrieve")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "welcome_email"
            }
        }


class TemplatePreviewRequest(BaseModel):
    """Request body for template preview"""
    sample_data: Dict[str, Any] = Field(
        description="Sample data to render the template with"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "sample_data": {
                    "shop_name": "My Fashion Store",
                    "product_count": 150
                }
            }
        }
        
class TemplateValidationRequest(BaseModel):
    """Request body for template validation"""
    subject: str = Field(description="Subject template to validate")
    body: str = Field(description="Body template to validate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Hello {{ shop_name }}!",
                "body": "<p>Welcome to {{ platform_name }}</p>"
            }
        }


class TemplateVariables(BaseModel):
    """Template variable requirements"""
    required: List[str] = Field(default_factory=list)
    optional: List[str] = Field(default_factory=list)


class TemplateResponse(BaseModel):
    """Basic template information"""
    type: str
    name: str
    category: str
    variables: TemplateVariables
    preview_available: bool = True


class TemplateListResponse(BaseModel):
    """Template list response"""
    templates: List[TemplateResponse]
    total: int


class TemplateDetailResponse(BaseModel):
    """Detailed template information"""
    type: str
    name: str
    category: str
    subject_template: str
    body_template: str
    variables: TemplateVariables
    global_variables: List[str]
    preview: Optional[Dict[str, Any]] = None


class TemplatePreviewResponse(BaseModel):
    """Template preview response"""
    subject: str
    body_html: str
    body_text: str
    missing_variables: List[str]
    unused_variables: List[str]
    all_variables: List[str]
    sample_data_used: Dict[str, Any]
    notification_type: str


class TemplateValidationResponse(BaseModel):
    """Template validation response"""
    is_valid: bool
    syntax_errors: List[str]
    warnings: List[str]

