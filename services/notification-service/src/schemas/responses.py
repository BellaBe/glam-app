from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, List, Any
from uuid import UUID
from datetime import datetime

class NotificationResponse(BaseModel):
    """Notification response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    shop_id: UUID
    shop_domain: str
    recipient_email: str
    type: str
    template_id: Optional[UUID]
    subject: str
    status: str
    provider: Optional[str]
    provider_message_id: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime
    metadata: Dict[str, Any]

class NotificationDetailResponse(NotificationResponse):
    """Detailed notification response"""
    content: str
    error_message: Optional[str]
    retry_count: int
    updated_at: datetime

class TemplateResponse(BaseModel):
    """Template response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    type: str
    subject_template: str
    body_template: str
    variables: Dict[str, List[str]]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class TemplatePreviewResponse(BaseModel):
    """Template preview response"""
    subject: str
    body_html: str
    body_text: str
    missing_variables: List[str]
    unused_variables: List[str]

class TemplateValidationResponse(BaseModel):
    """Template validation response"""
    is_valid: bool
    syntax_errors: List[Dict[str, Any]]
    warnings: List[str]

class PreferenceResponse(BaseModel):
    """Notification preference response"""
    model_config = ConfigDict(from_attributes=True)
    
    shop_id: UUID
    shop_domain: str
    email_enabled: bool
    notification_types: Dict[str, bool]
    unsubscribe_token: str
    created_at: datetime
    updated_at: datetime

class PaginatedResponse(BaseModel):
    """Base paginated response"""
    data: List[Any]
    meta: Dict[str, Any]
    pagination: Dict[str, Any]
    links: Dict[str, Optional[str]]