# services/token-service/src/repositories/token_repository.py

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from prisma import Prisma
from prisma.models import PlatformToken, TokenAccessLog
from shared.utils.logger import ServiceLogger

class TokenRepository:
    """Repository for token operations"""
    
    def __init__(self, prisma: Prisma, logger: ServiceLogger):
        self.prisma = prisma
        self.logger = logger
    
    async def upsert(self, data: Dict[str, Any]) -> PlatformToken:
        """Create or update token"""
        return await self.prisma.platformtoken.upsert(
            where={
                "merchant_id_platform_name": {
                    "merchant_id": data["merchant_id"],
                    "platform_name": data["platform_name"]
                }
            },
            update={
                "platform_shop_id": data["platform_shop_id"],
                "platform_domain": data["platform_domain"],
                "encrypted_token": data["encrypted_token"],
                "encryption_key_id": data["encryption_key_id"],
                "token_type": data["token_type"],
                "expires_at": data.get("expires_at"),
                "scopes": data.get("scopes"),
                "updated_at": datetime.utcnow()
            },
            create=data
        )
    
    async def find_by_merchant(self, merchant_id: str) -> List[PlatformToken]:
        """Find all tokens for a merchant"""
        return await self.prisma.platformtoken.find_many(
            where={"merchant_id": merchant_id}
        )
    
    async def find_by_merchant_platform(
        self, 
        merchant_id: str, 
        platform_name: str
    ) -> List[PlatformToken]:
        """Find tokens for merchant and platform"""
        return await self.prisma.platformtoken.find_many(
            where={
                "merchant_id": merchant_id,
                "platform_name": platform_name
            }
        )
    
    async def update_access(
        self, 
        token_id: str, 
        accessed_by: str
    ) -> None:
        """Update access tracking"""
        await self.prisma.platformtoken.update(
            where={"id": token_id},
            data={
                "last_accessed_by": accessed_by,
                "last_accessed_at": datetime.utcnow(),
                "access_count": {"increment": 1}
            }
        )
    
    async def delete(
        self, 
        merchant_id: str, 
        platform_name: str
    ) -> Optional[PlatformToken]:
        """Delete a token"""
        try:
            return await self.prisma.platformtoken.delete(
                where={
                    "merchant_id_platform_name": {
                        "merchant_id": merchant_id,
                        "platform_name": platform_name
                    }
                }
            )
        except Exception:
            return None
    
    async def log_access(
        self,
        token_id: str,
        accessed_by: str,
        access_type: str,
        success: bool,
        correlation_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> TokenAccessLog:
        """Log token access"""
        return await self.prisma.tokenaccesslog.create(
            data={
                "token_id": token_id,
                "accessed_by": accessed_by,
                "access_type": access_type,
                "success": success,
                "correlation_id": correlation_id,
                "ip_address": ip_address,
                "error_message": error_message
            }
        )