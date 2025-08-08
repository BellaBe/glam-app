import json
from typing import Optional, Dict, Any
from redis import asyncio as aioredis
from shared.utils.logger import ServiceLogger
from ..config import ServiceConfig

class CacheService:
    """Service for managing cached state"""
    
    def __init__(self, redis: aioredis.Redis, logger: ServiceLogger, config: ServiceConfig):
        self.redis = redis
        self.logger = logger
        self.config = config
    
    # Merchant Settings Cache
    async def set_merchant_settings(self, shop_domain: str, settings: Dict[str, Any]) -> None:
        """Cache merchant settings with TTL"""
        key = f"merchant:settings:{shop_domain}"
        await self.redis.setex(
            key,
            self.config.cache_ttl_settings,
            json.dumps(settings)
        )
        self.logger.debug(f"Cached settings for {shop_domain}")
    
    async def get_merchant_settings(self, shop_domain: str) -> Optional[Dict[str, Any]]:
        """Get cached merchant settings"""
        key = f"merchant:settings:{shop_domain}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    # Billing Entitlements Cache
    async def set_billing_entitlements(self, shop_domain: str, entitlements: Dict[str, Any]) -> None:
        """Cache billing entitlements with TTL"""
        key = f"billing:entitlements:{shop_domain}"
        await self.redis.setex(
            key,
            self.config.cache_ttl_entitlements,
            json.dumps(entitlements)
        )
        self.logger.debug(f"Cached entitlements for {shop_domain}")
    
    async def get_billing_entitlements(self, shop_domain: str) -> Optional[Dict[str, Any]]:
        """Get cached billing entitlements"""
        key = f"billing:entitlements:{shop_domain}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    # Combined check
    async def get_sync_allowed_state(self, shop_domain: str) -> tuple[bool, str]:
        """Check if sync is allowed based on cached state"""
        settings = await self.get_merchant_settings(shop_domain)
        if not settings:
            return False, "settings_missing"
        
        if not all([settings.get("dataAccess"), settings.get("autoSync"), settings.get("tos")]):
            return False, "settings_missing"
        
        entitlements = await self.get_billing_entitlements(shop_domain)
        if not entitlements or not entitlements.get("entitled"):
            return False, "not_entitled"
        
        return True, "ok"

# ================================================================
