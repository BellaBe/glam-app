# services/token-service/src/services/token_service.py

from typing import List, Optional, Dict, Any
from datetime import datetime
from shared.utils.logger import ServiceLogger
from shared.utils.exceptions import NotFoundError, ValidationError
from ..repositories.token_repository import TokenRepository
from ..services.encryption_service import EncryptionService
from ..schemas.token import StoreTokenRequest, TokenData
from ..utils.constants import SUPPORTED_PLATFORMS, TOKEN_TYPES

class TokenService:
    """Business logic for token operations"""
    
    def __init__(
        self,
        repository: TokenRepository,
        encryption: EncryptionService,
        logger: ServiceLogger
    ):
        self.repository = repository
        self.encryption = encryption
        self.logger = logger
    
    async def store_token(
        self,
        request: StoreTokenRequest,
        correlation_id: str
    ) -> str:
        """Store or update a token"""
        
        # Validate platform
        if request.platform_name not in SUPPORTED_PLATFORMS:
            raise ValidationError(
                f"Unsupported platform: {request.platform_name}",
                field="platform_name",
                value=request.platform_name
            )
        
        # Validate token type
        if request.token_type not in TOKEN_TYPES:
            raise ValidationError(
                f"Invalid token type: {request.token_type}",
                field="token_type",
                value=request.token_type
            )
        
        # Encrypt token data
        encrypted = self.encryption.encrypt(request.token_data)
        
        # Store in database
        token = await self.repository.upsert({
            "merchant_id": request.merchant_id,
            "platform_name": request.platform_name,
            "platform_shop_id": request.platform_shop_id,
            "shop_domain": request.shop_domain,
            "encrypted_token": encrypted,
            "encryption_key_id": self.encryption.key_id,
            "token_type": request.token_type,
            "expires_at": request.expires_at,
            "scopes": request.scopes
        })
        
        # Log access
        await self.repository.log_access(
            token_id=token.id,
            accessed_by=request.shop_domain,  # Store requester
            access_type="write",
            success=True,
            correlation_id=correlation_id
        )
        
        self.logger.info(
            f"Token stored for merchant {request.merchant_id}",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": request.merchant_id,
                "platform": request.platform_name
            }
        )
        
        return token.id
    
    async def get_tokens(
        self,
        merchant_id: str,
        platform: Optional[str],
        requesting_service: str,
        correlation_id: str,
        ip_address: Optional[str] = None
    ) -> List[TokenData]:
        """Retrieve and decrypt tokens for a merchant"""
        
        # Validate platform if specified
        if platform and platform not in SUPPORTED_PLATFORMS:
            raise ValidationError(
                f"Invalid platform: {platform}",
                field="platform",
                value=platform
            )
        
        # Retrieve tokens
        if platform:
            tokens = await self.repository.find_by_merchant_platform(
                merchant_id, platform
            )
        else:
            tokens = await self.repository.find_by_merchant(merchant_id)
        
        # Process each token
        result = []
        for token in tokens:
            # Decrypt token data
            try:
                token_data = self.encryption.decrypt(token.encrypted_token)
            except Exception as e:
                # Log decryption failure but continue
                await self.repository.log_access(
                    token_id=token.id,
                    accessed_by=requesting_service,
                    access_type="read",
                    success=False,
                    correlation_id=correlation_id,
                    ip_address=ip_address,
                    error_message=f"Decryption failed: {str(e)}"
                )
                continue
            
            # Update access tracking
            await self.repository.update_access(token.id, requesting_service)
            
            # Log successful access
            await self.repository.log_access(
                token_id=token.id,
                accessed_by=requesting_service,
                access_type="read",
                success=True,
                correlation_id=correlation_id,
                ip_address=ip_address
            )
            
            # Check expiry
            is_expired = token.expires_at and token.expires_at < datetime.utcnow()
            
            result.append(TokenData(
                platform_name=token.platform_name,
                platform_shop_id=token.platform_shop_id,
                shop_domain=token.shop_domain,
                token_data=token_data,
                token_type=token.token_type,
                expires_at=token.expires_at,
                is_expired=is_expired,
                scopes=token.scopes
            ))
        
        self.logger.info(
            f"Retrieved {len(result)} tokens for merchant {merchant_id}",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": merchant_id,
                "requesting_service": requesting_service,
                "token_count": len(result)
            }
        )
        
        return result
    
    async def delete_token(
        self,
        merchant_id: str,
        platform: str,
        correlation_id: str
    ) -> bool:
        """Delete a specific token"""
        
        # Validate platform
        if platform not in SUPPORTED_PLATFORMS:
            raise ValidationError(
                f"Invalid platform: {platform}",
                field="platform",
                value=platform
            )
        
        # Delete token
        deleted = await self.repository.delete(merchant_id, platform)
        
        if deleted:
            # Log deletion
            await self.repository.log_access(
                token_id=deleted.id,
                accessed_by=deleted.shop_domain,
                access_type="delete",
                success=True,
                correlation_id=correlation_id
            )
            
            self.logger.info(
                f"Token deleted for merchant {merchant_id} platform {platform}",
                extra={
                    "correlation_id": correlation_id,
                    "merchant_id": merchant_id,
                    "platform": platform
                }
            )
            return True
        
        return False