# -------------------------------
# services/notification-service/src/schemas/__init__.py
# -------------------------------

"""Request and response schemas for notification service."""

from .notification import (
    # Requests
    NotificationCreate,
    NotificationUpdate,
    BulkNotificationCreate,
    NotificationFilter,
    
    # Responses
    NotificationResponse,
    NotificationDetailResponse,
    NotificationListResponse,
)

from .template import (
    # Requests
    TemplateRequest,
    TemplatePreviewRequest,
    TemplateValidationRequest,
    
    # Responses
    TemplateResponse,
    TemplateDetailResponse,
    TemplateListResponse,
    TemplatePreviewResponse,
    TemplateValidationResponse,
)


from .common import (
    # Common schemas
    ShopInfo,
    PaginationParams,
    DateRangeFilter,
    SortOrder,
)

__all__ = [
    # Notification
    "NotificationCreate",
    "NotificationUpdate",
    "BulkNotificationCreate",
    "NotificationFilter",
    "NotificationResponse",
    "NotificationDetailResponse",
    "NotificationListResponse",
    
    # Template
    "TemplateRequest",
    "TemplatePreviewRequest",
    "TemplateValidationRequest",
    "TemplateResponse",
    "TemplateDetailResponse",
    "TemplateListResponse",
    "TemplatePreviewResponse",
    "TemplateValidationResponse",
    
    # Common
    "ShopInfo",
    "PaginationParams",
    "DateRangeFilter",
    "SortOrder",
]
