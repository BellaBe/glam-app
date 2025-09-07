# services/token-service/src/services/encryption_service.py

import json
import base64
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from shared.utils.logger import ServiceLogger
from shared.utils.exceptions import InternalError

class EncryptionService:
    """Handles token encryption and decryption"""
    
    def __init__(self, encryption_key: str, key_id: str, logger: ServiceLogger):
        self.key_id = key_id
        self.logger = logger
        self._cipher = self._create_cipher(encryption_key)
    
    def _create_cipher(self, key: str) -> Fernet:
        """Create Fernet cipher from key"""
        # Use PBKDF2 to derive a proper key from the string
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'token-service-salt',  # In production, use unique salt per key
            iterations=100000,
        )
        key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return Fernet(key_bytes)
    
    def encrypt(self, data: Dict[str, Any]) -> str:
        """Encrypt token data"""
        try:
            json_str = json.dumps(data)
            encrypted = self._cipher.encrypt(json_str.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.logger.exception(f"Encryption failed: {e}")
            raise InternalError(
                "Failed to encrypt token data",
                details={"error": str(e)}
            )
    
    def decrypt(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt token data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted.decode())
        except Exception as e:
            self.logger.exception(f"Decryption failed: {e}")
            raise InternalError(
                "Failed to decrypt token data",
                details={"error": str(e)}
            )