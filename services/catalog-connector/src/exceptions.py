# src/exceptions.py
from shared.errors import DomainError, ExternalServiceError, ValidationError

class ConnectorError(DomainError):
    """Base connector service error"""
    pass

class ShopifyAPIError(ExternalServiceError):
    """Shopify API error"""
    pass

class BulkOperationError(ConnectorError):
    """Bulk operation error"""
    pass

class BulkOperationTimeoutError(BulkOperationError):
    """Bulk operation timed out"""
    pass

class InvalidSyncRequestError(ValidationError):
    """Invalid sync request"""
    pass