# services/recommendation-service/src/services/season_compatibility_client.py
from typing import List, Dict, Optional
import httpx
from shared.utils.logger import ServiceLogger
from shared.utils.exceptions import ServiceUnavailableError, RequestTimeoutError


class SeasonCompatibilityClient:
    """Client for calling Season Compatibility Service"""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int,
        logger: ServiceLogger
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logger
    
    async def get_compatible_items(
        self,
        merchant_id: str,
        seasons: List[str],
        min_score: float,
        correlation_id: str
    ) -> List[Dict]:
        """Get compatible items from Season Compatibility Service"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Service-Name": "recommendation-service",
            "X-Correlation-ID": correlation_id
        }
        
        params = {
            "merchant_id": merchant_id,
            "seasons": ",".join(seasons),
            "min_score": min_score
        }
        
        url = f"{self.base_url}/api/v1/compatibility/items"
        
        self.logger.info(
            "Calling Season Compatibility Service",
            extra={
                "url": url,
                "merchant_id": merchant_id,
                "seasons": seasons,
                "correlation_id": correlation_id
            }
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("data", [])
                    self.logger.info(
                        f"Retrieved {len(items)} compatible items",
                        extra={"correlation_id": correlation_id}
                    )
                    return items
                else:
                    self.logger.error(
                        f"Season Compatibility Service error: {response.status_code}",
                        extra={"response": response.text}
                    )
                    raise ServiceUnavailableError(
                        message="Season Compatibility Service error",
                        service="season-compatibility",
                        details={"status": response.status_code}
                    )
                    
        except httpx.TimeoutException:
            raise RequestTimeoutError(
                message="Season Compatibility Service timeout",
                timeout_seconds=self.timeout,
                operation="get_compatible_items"
            )
        except httpx.RequestError as e:
            raise ServiceUnavailableError(
                message=f"Failed to connect to Season Compatibility Service: {e}",
                service="season-compatibility",
                retryable=True
            )