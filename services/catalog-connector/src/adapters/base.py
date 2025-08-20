# services/platform-connector/src/adapters/base.py
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional
from shared.utils.logger import ServiceLogger

class PlatformAdapter(ABC):
    """Base class for platform adapters"""
    
    def __init__(self, logger: ServiceLogger, config: dict):
        self.logger = logger
        self.config = config
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Any:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    async def fetch_products(
        self,
        merchant_id: str,
        platform_shop_id: str,
        shop_domain: str,
        sync_id: str,
        correlation_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Fetch products from platform.
        Yields batches of products.
        """
        pass
    
    @abstractmethod
    def transform_product(self, raw_product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform platform product to internal format"""
        pass
    
    def extract_id(self, gid: str) -> str:
        """Extract numeric ID from platform GID"""
        # e.g., "gid://shopify/Product/123456" -> "123456"
        if "/" in gid:
            return gid.split("/")[-1]
        return gid