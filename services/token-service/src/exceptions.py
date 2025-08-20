# services/token-service/src/exceptions.py

from shared.utils.exceptions import DomainError

class TokenExpiredError(DomainError):
    """Token has expired"""
    code = "TOKEN_EXPIRED"
    status = 401

class EncryptionKeyMismatchError(DomainError):
    """Token encrypted with different key"""
    code = "ENCRYPTION_KEY_MISMATCH"
    status = 500