# File: services/connector-service/src/models/base.py

"""Base model and common mixins for connector service models."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from cryptography.fernet import Fernet
from typing import Optional

# Import shared base and mixins
from shared.database.base import Base, TimestampedMixin


class EncryptedFieldMixin:
    """Mixin for encrypted fields."""
    
    _encryption_key: Optional[Fernet] = None
    
    @classmethod
    def set_encryption_key(cls, key: str):
        """Set the encryption key for all models."""
        cls._encryption_key = Fernet(key.encode())
    
    def encrypt(self, value: str) -> str:
        """Encrypt a value."""
        if not self._encryption_key:
            raise ValueError("Encryption key not set")
        return self._encryption_key.encrypt(value.encode()).decode()
    
    def decrypt(self, value: str) -> str:
        """Decrypt a value."""
        if not self._encryption_key:
            raise ValueError("Encryption key not set")
        return self._encryption_key.decrypt(value.encode()).decode()