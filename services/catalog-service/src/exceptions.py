from shared.utils.exceptions import (
    GlamBaseError,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    ServiceUnavailableError
)

class CatalogServiceError(GlamBaseError):
    """Base error for catalog service"""
    pass

class InvalidShopDomainError(ValidationError):
    """Invalid shop domain format"""
    pass

class SyncNotAllowedError(ForbiddenError):
    """Sync not allowed due to settings or entitlements"""
    pass

class SyncNotFoundError(NotFoundError):
    """Sync job not found"""
    pass

class SyncAlreadyActiveError(ConflictError):
    """Active sync already exists"""
    pass

class InvalidSyncTypeError(ValidationError):
    """Invalid sync type"""
    pass

class SyncFailedError(ServiceUnavailableError):
    """Sync operation failed"""
    pass

class EventProcessingError(ServiceUnavailableError):
    """Failed to process event"""
    pass

# ================================================================
