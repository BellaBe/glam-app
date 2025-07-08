# File: services/connector-service/src/clients/base.py

"""Base API client with retry and error handling."""

from typing import Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass
import httpx
import asyncio
from datetime import datetime

from shared.utils.logger import ServiceLogger


T = TypeVar('T')


@dataclass
class APIResponse(Generic[T]):
    """API response wrapper."""
    data: Optional[T] = None
    error: Optional[str] = None
    status_code: int = 200
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
    
    @property
    def success(self) -> bool:
        return self.error is None and 200 <= self.status_code < 300


class BaseAPIClient:
    """Base HTTP client with retry logic."""
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        logger: ServiceLogger = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logger
        
        # Create HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            follow_redirects=True
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        **kwargs
    ) -> APIResponse[Dict[str, Any]]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    **kwargs
                )
                
                # Return response for all status codes
                return APIResponse(
                    data=response.json() if response.content else None,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    error=None if response.is_success else response.reason_phrase
                )
                
            except httpx.TimeoutException as e:
                if self.logger:
                    self.logger.warning(
                        f"Request timeout (attempt {attempt + 1}/{self.max_retries}): {url}"
                    )
                if attempt == self.max_retries - 1:
                    return APIResponse(error=f"Request timeout: {str(e)}", status_code=0)
                    
            except httpx.NetworkError as e:
                if self.logger:
                    self.logger.warning(
                        f"Network error (attempt {attempt + 1}/{self.max_retries}): {url}"
                    )
                if attempt == self.max_retries - 1:
                    return APIResponse(error=f"Network error: {str(e)}", status_code=0)
                    
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                return APIResponse(error=f"Unexpected error: {str(e)}", status_code=0)
            
            # Exponential backoff for retries
            if attempt < self.max_retries - 1:
                delay = self.backoff_factor ** attempt
                await asyncio.sleep(delay)
        
        return APIResponse(error="Max retries exceeded", status_code=0)
    
    async def get(self, endpoint: str, **kwargs) -> APIResponse[Dict[str, Any]]:
        """GET request."""
        return await self._request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> APIResponse[Dict[str, Any]]:
        """POST request."""
        return await self._request("POST", endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> APIResponse[Dict[str, Any]]:
        """PUT request."""
        return await self._request("PUT", endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> APIResponse[Dict[str, Any]]:
        """DELETE request."""
        return await self._request("DELETE", endpoint, **kwargs)
