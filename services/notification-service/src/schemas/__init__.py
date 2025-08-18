# -------------------------------
# services/notification-service/src/schemas/__init__.py
# -------------------------------

"""Request and response schemas for notification service."""

from .common import (
    DateRangeFilter,
    PaginationParams,
    # Common schemas
    ShopInfo,
    SortOrder,
)
from .notification import (
    BulkNotificationCreate,
    # Requests
    NotificationCreate,
    NotificationDetailResponse,
    NotificationFilter,
    NotificationListResponse,
    # Responses
    NotificationResponse,
    NotificationUpdate,
)
from .template import (
    TemplateDetailResponse,
    TemplateListResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    # Requests
    TemplateRequest,
    # Responses
    TemplateResponse,
    TemplateValidationRequest,
    TemplateValidationResponse,
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
