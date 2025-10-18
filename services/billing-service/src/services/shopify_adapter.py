# services/billing-service/src/services/shopify_adapter.py

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from shared.utils.logger import ServiceLogger

    from ..config import ServiceConfig
    from ..db.models import BillingAccount, Payment, PricingProduct


class ShopifyAdapter:
    """Adapter for Shopify billing API"""

    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self.api_version = config.shopify_api_version
        self.test_mode = config.shopify_test_mode

    async def create_charge(
        self,
        account: BillingAccount,
        payment: Payment,
        product: PricingProduct,
        return_url: str,
    ) -> str:
        """Create Shopify application charge"""

        # Get access token (from token service)
        access_token = await self._get_access_token(account.merchant_id)

        # Build charge request
        charge_data = {
            "application_charge": {
                "name": payment.description,
                "price": str(payment.amount),
                "return_url": return_url,
                "test": self.test_mode,
            }
        }

        # Call Shopify API
        url = f"https://{account.platform_domain}/admin/api/{self.api_version}/application_charges.json"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers={
                        "X-Shopify-Access-Token": access_token,
                        "Content-Type": "application/json",
                    },
                    json=charge_data,
                    timeout=10.0,
                )

                if response.status_code != 201:
                    self.logger.error(f"Shopify charge creation failed: {response.text}")
                    raise Exception(f"Shopify API error: {response.status_code}")

                charge = response.json()["application_charge"]

                # Update payment with platform charge ID
                # This would be done in the service layer
                # payment.platform_charge_id = str(charge["id"])

                return charge["confirmation_url"]

            except httpx.TimeoutException as e:
                self.logger.error(f"Shopify API timeout: {e}")
                raise Exception("Platform API timeout") from e
            except Exception as e:
                self.logger.error(f"Shopify charge creation failed: {e}")
                raise

    async def _get_access_token(self, merchant_id: str) -> str:
        """Get Shopify access token from token service"""
        # TODO: Implement token service call
        # For now, return placeholder
        return "test_token"
