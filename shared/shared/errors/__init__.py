"""
Shared error handling module for glam-app microservices.

This module provides a consistent error hierarchy and handling patterns
across all services, following the three-tier model:
- BaseError (root)
- InfrastructureError (external failures)
- DomainError (business logic failures)
"""

from .base import (
    GlamBaseError,
    InfrastructureError,
    DomainError,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitedError,
    ServiceUnavailableError,
    TimeoutError,
    InternalError,
)

from .catalog import (
    SyncInProgressError,
    SyncNotFoundError,
    SyncNotResumableError,
    SyncNotCancellableError,
    ItemNotFoundError,
    ParentSyncNotFoundError,
)

from .profile import (
    ProfileNotFoundError,
    ProfileAlreadyExistsError,
    ProfileCreationFailedError,
)

from .analysis import (
    AnalysisInProgressError,
    AnalysisNotFoundError,
    AnalysisNotCancellableError,
    NoCurrentAnalysisError,
)

from .selfie import (
    SelfieNotFoundError,
    InvalidImageFormatError,
    ImageTooLargeError,
    ImageTooSmallError,
    NoFaceDetectedError,
    MultipleFacesDetectedError,
    PoorImageQualityError,
)

from .notification import (
    NotificationNotFoundError,
    TemplateNotFoundError,
    TemplateRenderError,
    InvalidRecipientError,
    PreferencesNotFoundError,
    EmailProviderError,
    UnsubscribedError,
)

from .infrastructure import (
    DatabaseError,
    RedisError,
    S3Error,
    UpstreamServiceError,
    CircuitOpenError,
    MessageBusError,
)

from .handlers import (
    ErrorResponse,
    create_error_response,
    exception_to_error_response,
)

from .utils import (
    wrap_external_error,
    classify_http_error,
    is_retryable_error,
)

__all__ = [
    # Base errors
    "GlamBaseError",
    "InfrastructureError",
    "DomainError",
    
    # Common domain errors
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "RateLimitedError",
    "ServiceUnavailableError",
    "TimeoutError",
    "InternalError",
    
    # Catalog errors
    "SyncInProgressError",
    "SyncNotFoundError",
    "SyncNotResumableError",
    "SyncNotCancellableError",
    "ItemNotFoundError",
    "ParentSyncNotFoundError",
    
    # Profile errors
    "ProfileNotFoundError",
    "ProfileAlreadyExistsError",
    "ProfileCreationFailedError",
    
    # Analysis errors
    "AnalysisInProgressError",
    "AnalysisNotFoundError",
    "AnalysisNotCancellableError",
    "NoCurrentAnalysisError",
    
    # Selfie errors
    "SelfieNotFoundError",
    "InvalidImageFormatError",
    "ImageTooLargeError",
    "ImageTooSmallError",
    "NoFaceDetectedError",
    "MultipleFacesDetectedError",
    "PoorImageQualityError",
    
    # Notification errors
    "NotificationNotFoundError",
    "TemplateNotFoundError",
    "TemplateRenderError",
    "InvalidRecipientError",
    "PreferencesNotFoundError",
    "EmailProviderError",
    "UnsubscribedError",
    
    # Infrastructure errors
    "DatabaseError",
    "RedisError",
    "S3Error",
    "UpstreamServiceError",
    "CircuitOpenError",
    "MessageBusError",
    
    # Handlers and utilities
    "ErrorResponse",
    "create_error_response",
    "exception_to_error_response",
    "wrap_external_error",
    "classify_http_error",
    "is_retryable_error",
]
