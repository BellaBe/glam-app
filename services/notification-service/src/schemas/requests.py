from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Dict, List, Any
from uuid import UUID

class NotificationCreate(BaseModel):
    """Create notification request"""
    shop_id: UUID
    shop_domain: str
    recipient_email: EmailStr
    notification_type: str
    template_id: Optional[UUID] = None
    dynamic_content: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BulkNotificationCreate(BaseModel):
    """Bulk notification request"""
    template_id: UUID
    notification_type: str
    recipients: List[Dict[str, Any]]
    
    @field_validator('recipients')
    def validate_recipients(cls, v):
        if not v:
            raise ValueError('Recipients list cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot send to more than 100 recipients at once')
        return v

class TemplateCreate(BaseModel):
    """Create template request"""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    subject_template: str = Field(..., min_length=1, max_length=255)
    body_template: str = Field(..., min_length=1)
    variables: Dict[str, List[str]] = Field(default_factory=lambda: {"required": [], "optional": []})
    description: Optional[str] = None
    is_active: bool = True
    
    @field_validator('name')
    def validate_name(cls, v):
        # Only allow alphanumeric, underscore, and hyphen
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Name must only contain alphanumeric characters, underscores, and hyphens')
        return v
    
    @field_validator('variables')
    def validate_variables(cls, v):
        if 'required' not in v:
            v['required'] = []
        if 'optional' not in v:
            v['optional'] = []
        return v

class TemplateUpdate(BaseModel):
    """Update template request"""
    subject_template: Optional[str] = Field(None, min_length=1, max_length=255)
    body_template: Optional[str] = Field(None, min_length=1)
    variables: Optional[Dict[str, List[str]]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class TemplatePreview(BaseModel):
    """Preview template request"""
    dynamic_content: Dict[str, Any] = Field(default_factory=dict)

class TemplateClone(BaseModel):
    """Clone template request"""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    

class PreferenceUpdate(BaseModel):
    """Update notification preferences"""
    shop_id: UUID
    shop_domain: str
    email_enabled: bool = True
    notification_types: Dict[str, bool] = Field(default_factory=dict)
    
class PreferenceCreate(BaseModel):
    """Create new notification preferences"""
    shop_id: UUID
    shop_domain: str
    email_enabled: bool = True
    notification_types: Optional[Dict[str, bool]] = Field(
        default_factory=lambda: {
            "order_confirmation": True,
            "order_shipped": True,
            "order_delivered": True,
            "customer_welcome": True,
            "abandoned_cart": True,
            "marketing": False
        }
    )