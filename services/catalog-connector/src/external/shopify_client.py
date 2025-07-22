# src/services/shopify_client.py
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from shared.utils.logger import ServiceLogger
from ..config import ConnectorServiceConfig
from ..exceptions import ShopifyAPIError

class ShopifyGraphQLClient:
    """Shopify GraphQL API client with rate limiting"""
    
    def __init__(self, config: ConnectorServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self.client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = asyncio.Semaphore(config.shopify_rate_limit_per_sec)
        self._rate_limit_window = asyncio.Semaphore(1)
        self._last_request_time = 0.0
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def execute_query(
        self, 
        shop_domain: str,
        access_token: str,
        query: str, 
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query with rate limiting"""
        if not self.client:
            raise ShopifyAPIError("Client not initialized")
        
        # Rate limiting
        async with self._rate_limiter:
            await self._enforce_rate_limit()
            
            url = f"https://{shop_domain}/admin/api/{self.config.shopify_api_version}/graphql.json"
            
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            try:
                response = await self.client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if "errors" in data:
                    error_msg = "; ".join([err.get("message", "Unknown error") for err in data["errors"]])
                    raise ShopifyAPIError(f"GraphQL errors: {error_msg}")
                
                return data
                
            except httpx.HTTPStatusError as e:
                raise ShopifyAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
            except Exception as e:
                raise ShopifyAPIError(f"Request failed: {str(e)}")
    
    async def start_bulk_operation(
        self,
        shop_domain: str,
        access_token: str,
        query: str
    ) -> Dict[str, Any]:
        """Start a bulk operation"""
        mutation = """
        mutation bulkOperationRunQuery($query: String!) {
          bulkOperationRunQuery(query: $query) {
            bulkOperation {
              id
              status
              createdAt
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {"query": query}
        result = await self.execute_query(shop_domain, access_token, mutation, variables)
        
        bulk_data = result["data"]["bulkOperationRunQuery"]
        
        if bulk_data["userErrors"]:
            errors = [err["message"] for err in bulk_data["userErrors"]]
            raise ShopifyAPIError(f"Bulk operation start failed: {'; '.join(errors)}")
        
        return bulk_data["bulkOperation"]
    
    async def get_bulk_operation_status(
        self,
        shop_domain: str,
        access_token: str,
        bulk_operation_id: str
    ) -> Dict[str, Any]:
        """Get bulk operation status"""
        query = """
        query getBulkOperation($id: ID!) {
          node(id: $id) {
            ... on BulkOperation {
              id
              status
              errorCode
              createdAt
              completedAt
              objectCount
              fileSize
              url
              partialDataUrl
            }
          }
        }
        """
        
        variables = {"id": bulk_operation_id}
        result = await self.execute_query(shop_domain, access_token, query, variables)
        
        return result["data"]["node"]
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        min_interval = 1.0 / self.config.shopify_rate_limit_per_sec
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self._last_request_time = asyncio.get_event_loop().time()