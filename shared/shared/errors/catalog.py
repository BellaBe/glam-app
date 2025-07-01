
# -------------------------------
# shared/errors/catalog.py
# -------------------------------

"""Catalog service specific errors."""

from typing import Optional
from .base import ConflictError, NotFoundError


class SyncInProgressError(ConflictError):
    """Another sync operation is already running."""
    
    code = "SYNC_IN_PROGRESS"
    
    def __init__(
        self,
        message: str = "Another sync is already in progress",
        *,
        current_sync_id: Optional[str] = None,
        merchant_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if current_sync_id:
            self.details["current_sync_id"] = current_sync_id
        if merchant_id:
            self.details["merchant_id"] = merchant_id


class SyncNotFoundError(NotFoundError):
    """Sync operation not found."""
    
    code = "SYNC_NOT_FOUND"
    
    def __init__(
        self,
        message: str,
        *,
        sync_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, resource="sync", resource_id=sync_id, **kwargs)


class SyncNotResumableError(ConflictError):
    """Sync cannot be resumed in its current state."""
    
    code = "SYNC_NOT_RESUMABLE"
    
    def __init__(
        self,
        message: str,
        *,
        sync_id: Optional[str] = None,
        sync_status: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if sync_id:
            self.details["sync_id"] = sync_id
        if sync_status:
            self.details["sync_status"] = sync_status
        if reason:
            self.details["reason"] = reason


class SyncNotCancellableError(ConflictError):
    """Sync cannot be cancelled in its current state."""
    
    code = "SYNC_NOT_CANCELLABLE"
    
    def __init__(
        self,
        message: str,
        *,
        sync_id: Optional[str] = None,
        sync_status: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if sync_id:
            self.details["sync_id"] = sync_id
        if sync_status:
            self.details["sync_status"] = sync_status


class ItemNotFoundError(NotFoundError):
    """Item not found in catalog."""
    
    code = "ITEM_NOT_FOUND"
    
    def __init__(
        self,
        message: str,
        *,
        item_id: Optional[str] = None,
        merchant_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, resource="item", resource_id=item_id, **kwargs)
        
        if merchant_id:
            self.details["merchant_id"] = merchant_id


class ParentSyncNotFoundError(NotFoundError):
    """Parent sync operation not found for resume."""
    
    code = "PARENT_SYNC_NOT_FOUND"
    
    def __init__(
        self,
        message: str,
        *,
        parent_sync_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            resource="parent_sync",
            resource_id=parent_sync_id,
            **kwargs
        )
