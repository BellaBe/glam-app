# services/catalog-ai-analyzer/src/exceptions.py
from typing import Optional, Any, Dict
from shared.utils.exceptions import (
    DomainError, 
    InfrastructureError,
    ValidationError
)

# ===============================
# Domain Errors (Business Logic)
# ===============================

class CatalogAnalysisError(DomainError):
    """Base error for catalog analysis domain"""
    code = "CATALOG_ANALYSIS_ERROR"

class ImageAnalysisError(CatalogAnalysisError):
    """Error during image analysis"""
    code = "CAT_IMG_ANALYSIS_FAILED"
    
    def __init__(
        self,
        message: str,
        *,
        item_id: Optional[str] = None,
        product_id: Optional[str] = None,
        variant_id: Optional[str] = None,
        analyzer: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        if item_id:
            self.details["item_id"] = item_id
        if product_id:
            self.details["product_id"] = product_id
        if variant_id:
            self.details["variant_id"] = variant_id
        if analyzer:
            self.details["analyzer"] = analyzer

class ImageDownloadError(CatalogAnalysisError):
    """Failed to download image"""
    code = "CAT_IMG_DOWNLOAD_FAILED"
    
    def __init__(
        self,
        message: str,
        *,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        if url:
            self.details["url"] = url
        if status_code:
            self.details["status_code"] = status_code

class InvalidImageFormatError(ValidationError):
    """Invalid image format"""
    code = "CAT_IMG_INVALID_FORMAT"
    
    def __init__(
        self,
        message: str,
        *,
        format_received: Optional[str] = None,
        formats_supported: Optional[list] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        if format_received:
            self.details["format_received"] = format_received
        if formats_supported:
            self.details["formats_supported"] = formats_supported

class ColorExtractionError(ImageAnalysisError):
    """MediaPipe color extraction failed"""
    code = "CAT_COLOR_EXTRACTION_FAILED"
    
    def __init__(
        self,
        message: str = "Failed to extract colors from image",
        **kwargs
    ):
        super().__init__(message, analyzer="mediapipe", **kwargs)

class MissingProductIdentifiersError(ValidationError):
    """Missing required product/variant IDs"""
    code = "CAT_MISSING_IDS"
    
    def __init__(
        self,
        message: str = "Missing product_id or variant_id",
        *,
        item_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        if item_id:
            self.details["item_id"] = item_id

class BatchSizeExceededError(ValidationError):
    """Batch size exceeds maximum allowed"""
    code = "CAT_BATCH_SIZE_EXCEEDED"
    
    def __init__(
        self,
        message: str,
        *,
        batch_size: int,
        max_size: int,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.details["batch_size"] = batch_size
        self.details["max_size"] = max_size

# ===============================
# Infrastructure Errors
# ===============================

class OpenAIAPIError(InfrastructureError):
    """OpenAI API error"""
    code = "CAT_OPENAI_API_ERROR"
    
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, service="openai", **kwargs)
        if status_code:
            self.details["status_code"] = status_code
        if error_type:
            self.details["error_type"] = error_type

class OpenAIRateLimitError(OpenAIAPIError):
    """OpenAI rate limit exceeded"""
    code = "CAT_OPENAI_RATE_LIMITED"
    
    def __init__(
        self,
        message: str = "OpenAI API rate limit exceeded",
        *,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, retryable=True, **kwargs)
        if retry_after:
            self.details["retry_after"] = retry_after

class AnalysisTimeoutError(InfrastructureError):
    """Analysis timeout"""
    code = "CAT_ANALYSIS_TIMEOUT"
    
    def __init__(
        self,
        message: str,
        *,
        timeout_seconds: int,
        item_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message, 
            service="analyzer",
            retryable=True,
            timeout_seconds=timeout_seconds,
            **kwargs
        )
        if item_id:
            self.details["item_id"] = item_id

class BothAnalyzersFailedError(ImageAnalysisError):
    """Both MediaPipe and OpenAI analyzers failed"""
    code = "CAT_BOTH_ANALYZERS_FAILED"
    
    def __init__(
        self,
        message: str = "Complete analysis failure - both analyzers failed",
        *,
        mediapipe_error: Optional[str] = None,
        openai_error: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.details["failures"] = {}
        if mediapipe_error:
            self.details["failures"]["mediapipe"] = mediapipe_error
        if openai_error:
            self.details["failures"]["openai"] = openai_error

# ===============================
# Utility Functions
# ===============================

def is_retryable_error(error: Exception) -> bool:
    """Check if an error should be retried"""
    if isinstance(error, InfrastructureError):
        return error.retryable
    
    # Specific error types that should be retried
    retryable_types = (
        OpenAIRateLimitError,
        AnalysisTimeoutError,
        ImageDownloadError,
    )
    
    return isinstance(error, retryable_types)

def get_error_code(error: Exception) -> str:
    """Extract error code from exception"""
    if hasattr(error, 'code'):
        return error.code
    return "UNKNOWN_ERROR"