# services/platform-connector/src/services/token_service.py
import aiohttp
from typing import Optional, Dict, Any
from shared.utils.logger import ServiceLogger
from shared.utils.exceptions import (
    InfrastructureError,
    NotFoundError,
    UnauthorizedError
)
from shared.api.correlation import add_correlation_header

class TokenServiceClient:
    """Client for interacting with Token Service"""
    
    def __init__(self, logger: ServiceLogger, config: dict):
        self.logger = logger
        self.base_url = config.get("token_service_url", "http://token-service:8000")
        self.timeout = config.get("token_service_timeout", 10)
    
    async def get_shopify_token(
        self,
        shop_domain: str,
        correlation_id: str
    ) -> str:
        """Get Shopify access token from Token Service"""
        
        url = f"{self.base_url}/api/v1/tokens/shopify/{shop_domain}"
        headers = add_correlation_header({
            "Content-Type": "application/json"
        })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 404:
                        raise NotFoundError(
                            f"Shopify token not found for shop: {shop_domain}",
                            resource="shopify_token",
                            resource_id=shop_domain
                        )
                    
                    if response.status == 401:
                        raise UnauthorizedError(
                            "Unauthorized to access Token Service"
                        )
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Extract token from response
                    token = data.get("data", {}).get("access_token")
                    if not token:
                        raise InfrastructureError(
                            "Token Service returned empty token",
                            service="token-service"
                        )
                    
                    self.logger.debug(
                        f"Retrieved Shopify token for {shop_domain}",
                        extra={
                            "correlation_id": correlation_id,
                            "shop_domain": shop_domain
                        }
                    )
                    
                    return token
                    
        except aiohttp.ClientError as e:
            raise InfrastructureError(
                f"Failed to connect to Token Service: {e}",
                service="token-service",
                retryable=True
            )
    
    async def get_woocommerce_credentials(
        self,
        domain: str,
        correlation_id: str
    ) -> Dict[str, str]:
        """Get WooCommerce API credentials from Token Service"""
        
        url = f"{self.base_url}/api/v1/tokens/woocommerce/{domain}"
        headers = add_correlation_header({
            "Content-Type": "application/json"
        })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 404:
                        raise NotFoundError(
                            f"WooCommerce credentials not found for: {domain}",
                            resource="woocommerce_credentials",
                            resource_id=domain
                        )
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Extract credentials
                    creds = data.get("data", {})
                    if not creds.get("consumer_key") or not creds.get("consumer_secret"):
                        raise InfrastructureError(
                            "Token Service returned incomplete credentials",
                            service="token-service"
                        )
                    
                    return {
                        "consumer_key": creds["consumer_key"],
                        "consumer_secret": creds["consumer_secret"]
                    }
                    
        except aiohttp.ClientError as e:
            raise InfrastructureError(
                f"Failed to connect to Token Service: {e}",
                service="token-service",
                retryable=True
            )
        