# src/exceptions.py
from shared.errors import DomainError, NotFoundError, ValidationError

class CatalogError(DomainError):
    """Base catalog service error"""
    pass

class SyncOperationNotFoundError(NotFoundError):
    """Sync operation not found"""
    pass

class SyncOperationAlreadyRunningError(ValidationError):
    """Sync operation already running"""
    pass

class ItemNotFoundError(NotFoundError):
    """Catalog item not found"""
    pass

class InvalidSyncTypeError(ValidationError):
    """Invalid sync type"""
    pass