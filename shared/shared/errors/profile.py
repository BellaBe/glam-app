
# -------------------------------
# shared/errors/profile.py
# -------------------------------

"""Profile service specific errors."""

from typing import Optional
from .base import NotFoundError, ConflictError, DomainError


class ProfileNotFoundError(NotFoundError):
    """User profile not found."""
    
    code = "PROFILE_NOT_FOUND"
    
    def __init__(
        self,
        message: str,
        *,
        user_id: Optional[str] = None,
        profile_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, resource="profile", **kwargs)
        
        if user_id:
            self.details["user_id"] = user_id
        if profile_id:
            self.details["profile_id"] = profile_id


class ProfileAlreadyExistsError(ConflictError):
    """Profile already exists for this user."""
    
    code = "PROFILE_ALREADY_EXISTS"
    
    def __init__(
        self,
        message: str,
        *,
        user_id: Optional[str] = None,
        existing_profile_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            conflicting_resource="profile",
            **kwargs
        )
        
        if user_id:
            self.details["user_id"] = user_id
        if existing_profile_id:
            self.details["existing_profile_id"] = existing_profile_id


class ProfileCreationFailedError(DomainError):
    """Failed to create profile."""
    
    code = "PROFILE_CREATION_FAILED"
    status = 422
    
    def __init__(
        self,
        message: str,
        *,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        
        if user_id:
            self.details["user_id"] = user_id
        if reason:
            self.details["reason"] = reason

