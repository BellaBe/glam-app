
# -------------------------------
# shared/errors/analysis.py
# -------------------------------

"""Analysis service specific errors."""

from typing import Optional
from .base import ConflictError, NotFoundError


class AnalysisInProgressError(ConflictError):
    """Another analysis is already in progress."""
    
    code = "ANALYSIS_IN_PROGRESS"
    
    def __init__(
        self,
        message: str = "Another analysis is already in progress",
        *,
        current_analysis_id: Optional[str] = None,
        user_id: Optional[str] = None,
        started_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if current_analysis_id:
            self.details["current_analysis_id"] = current_analysis_id
        if user_id:
            self.details["user_id"] = user_id
        if started_at:
            self.details["started_at"] = started_at


class AnalysisNotFoundError(NotFoundError):
    """Analysis not found."""
    
    code = "ANALYSIS_NOT_FOUND"
    
    def __init__(
        self,
        message: str,
        *,
        analysis_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, resource="analysis", resource_id=analysis_id, **kwargs)
        
        if user_id:
            self.details["user_id"] = user_id


class AnalysisNotCancellableError(ConflictError):
    """Analysis cannot be cancelled in its current state."""
    
    code = "ANALYSIS_NOT_CANCELLABLE"
    
    def __init__(
        self,
        message: str,
        *,
        analysis_id: Optional[str] = None,
        current_status: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if analysis_id:
            self.details["analysis_id"] = analysis_id
        if current_status:
            self.details["current_status"] = current_status
        if reason:
            self.details["reason"] = reason


class NoCurrentAnalysisError(NotFoundError):
    """No completed analysis available."""
    
    code = "NO_CURRENT_ANALYSIS"
    
    def __init__(
        self,
        message: str = "No completed analysis available",
        *,
        user_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, resource="current_analysis", **kwargs)
        
        if user_id:
            self.details["user_id"] = user_id
