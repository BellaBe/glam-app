# File: services/connector-service/src/clients/shopify_client.py

"""Shopify API client implementation."""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

from .base import BaseAPIClient, APIResponse
from ..exceptions import ShopifyAPIError, RateLimitExceededError


class ShopifyClient(BaseAPIClient):
    """Shopify-specific API client."""
    
    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str = "2024-01",
        **kwargs
    ):
        # Build base URL
        base_url = f"https://{shop_domain}/admin/api/{api_version}"
        super().__init__(base_url=base_url, **kwargs)
        
        # Set default headers
        self._default_headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
    
    def _parse_rate_limit(self, headers: Dict[str, str]) -> Tuple[int, int]:
        """Parse Shopify rate limit headers."""
        # Format: "current/limit" e.g., "32/40"
        rate_limit_header = headers.get("X-Shopify-Shop-Api-Call-Limit", "0/40")
        match = re.match(r"(\d+)/(\d+)", rate_limit_header)
        if match:
            current = int(match.group(1))
            limit = int(match.group(2))
            return current, limit
        return 0, 40
    
    def _parse_link_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Parse pagination info from Link header."""
        link_header = headers.get("Link", "")
        if not link_header:
            return None
            
        # Parse Link header for next page
        # Format: <...page_info=xyz>; rel="next"
        match = re.search(r'page_info=([^&>]+).*?rel="next"', link_header)
        if match:
            return match.group(1)
        return None
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> APIResponse[Dict[str, Any]]:
        """Override to handle Shopify-specific logic."""
        # Add default headers
        headers = kwargs.get("headers", {})
        headers.update(self._default_headers)
        kwargs["headers"] = headers
        
        # Make request
        response = await super()._request(method, endpoint, **kwargs)
        
        # Check rate limits
        if response.headers:
            current, limit = self._parse_rate_limit(response.headers)
            if current >= limit * 0.8:  # 80% threshold
                if self.logger:
                    self.logger.warning(
                        f"Approaching rate limit: {current}/{limit}",
                        extra={"endpoint": endpoint}
                    )
        
        # Handle specific status codes
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitExceededError(
                store_id=self.base_url.split("/")[2],
                retry_after=retry_after
            )
        elif response.status_code == 401:
            raise ShopifyAPIError(
                "Invalid access token",
                status_code=401,
                response_body=str(response.data)
            )
        elif response.status_code >= 400:
            raise ShopifyAPIError(
                f"Shopify API error: {response.error}",
                status_code=response.status_code,
                response_body=str(response.data)
            )
        
        return response
    
    async def get_products(
        self,
        limit: int = 250,
        page_info: Optional[str] = None,
        fields: Optional[List[str]] = None,
        updated_at_min: Optional[datetime] = None,
        **params
    ) -> APIResponse[Dict[str, Any]]:
        """Get products with pagination."""
        query_params = {
            "limit": min(limit, 250),  # Shopify max is 250
            **params
        }
        
        if page_info:
            query_params["page_info"] = page_info
            
        if fields:
            query_params["fields"] = ",".join(fields)
            
        if updated_at_min:
            query_params["updated_at_min"] = updated_at_min.isoformat()
        
        response = await self.get("/products.json", params=query_params)
        
        # Add pagination info to response
        if response.success and response.headers:
            next_cursor = self._parse_link_header(response.headers)
            if next_cursor and response.data:
                response.data["next_cursor"] = next_cursor
                
        return response
    
    async def get_product_count(self, **params) -> APIResponse[Dict[str, Any]]:
        """Get total product count."""
        return await self.get("/products/count.json", params=params)
    
    async def get_product(self, product_id: str, fields: Optional[List[str]] = None) -> APIResponse[Dict[str, Any]]:
        """Get single product by ID."""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
            
        return await self.get(f"/products/{product_id}.json", params=params)
