import httpx

from shared.utils.logger import ServiceLogger

from ..config import ServiceConfig
from ..exceptions import PlatformCheckoutError


class ShopifyClient:
    """Simplified Shopify API client for billing"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self.api_version = config.shopify_api_version

    async def create_charge(self, domain: str, amount: str, name: str, return_url: str) -> dict:
        """Create Shopify recurring charge"""
        try:
            # This is a simplified implementation
            # In production, you'd use proper Shopify API calls
            charge_data = {
                "recurring_application_charge": {
                    "name": name,
                    "price": str(amount),
                    "return_url": return_url,
                    "test": self.config.environment != "prod",
                }
            }

            # Mock response for development
            if self.config.debug:
                return {
                    "charge_id": f"charge_{domain}_{amount}",
                    "confirmation_url": f"https://{domain}/admin/charges/confirm",
                }

            # Real Shopify API call would go here
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{domain}/admin/api/{self.api_version}/recurring_application_charges.json",
                    json=charge_data,
                    headers={
                        "X-Shopify-Access-Token": "shop_access_token",  # Would come from merchant record
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code != 201:
                    raise PlatformCheckoutError("shopify", response.text)

                data = response.json()
                return {
                    "charge_id": data["recurring_application_charge"]["id"],
                    "confirmation_url": data["recurring_application_charge"]["confirmation_url"],
                }

        except httpx.RequestError as e:
            self.logger.exception(f"Shopify API error: {e}")
            raise PlatformCheckoutError("shopify", str(e)) from e
