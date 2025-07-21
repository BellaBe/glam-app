# services/billing-service/src/external/shopify_billing_client.py
import httpx
from typing import Dict, Any
from decimal import Decimal

from ..models import BillingInterval
from ..exceptions import ShopifyBillingError

class ShopifyBillingClient:
    """Shopify billing operations client"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
    
    async def create_subscription(
        self,
        shop_id: str,
        plan_name: str,
        amount: Decimal,
        credits: int,
        billing_interval: BillingInterval,
        return_url: str,
        test_mode: bool = False
    ) -> Dict[str, Any]:
        """Create recurring subscription charge via Shopify GraphQL"""
        mutation = """
        mutation AppSubscriptionCreate($name: String!, $lineItems: [AppSubscriptionLineItemInput!]!, $returnUrl: URL!, $test: Boolean) {
          appSubscriptionCreate(name: $name, lineItems: $lineItems, returnUrl: $returnUrl, test: $test) {
            appSubscription {
              id
              status
              createdAt
            }
            confirmationUrl
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "name": f"{plan_name} - {credits} Credits",
            "lineItems": [{
                "plan": {
                    "appRecurringPricingDetails": {
                        "price": {"amount": str(amount), "currencyCode": "USD"},
                        "interval": billing_interval.value
                    }
                }
            }],
            "returnUrl": return_url,
            "test": test_mode
        }
        
        response = await self._make_graphql_request(shop_id, mutation, variables)
        
        if response["data"]["appSubscriptionCreate"]["userErrors"]:
            errors = response["data"]["appSubscriptionCreate"]["userErrors"]
            raise ShopifyBillingError(f"Subscription creation failed: {errors}")
        
        return response["data"]["appSubscriptionCreate"]
    
    async def create_one_time_charge(
        self,
        shop_id: str,
        amount: Decimal,
        description: str,
        return_url: str,
        test_mode: bool = False
    ) -> Dict[str, Any]:
        """Create one-time charge via Shopify GraphQL"""
        mutation = """
        mutation AppPurchaseOneTimeCreate($name: String!, $price: MoneyInput!, $returnUrl: URL!, $test: Boolean) {
          appPurchaseOneTimeCreate(name: $name, price: $price, returnUrl: $returnUrl, test: $test) {
            appPurchaseOneTime {
              id
              status
              createdAt
            }
            confirmationUrl
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "name": description,
            "price": {"amount": str(amount), "currencyCode": "USD"},
            "returnUrl": return_url,
            "test": test_mode
        }
        
        response = await self._make_graphql_request(shop_id, mutation, variables)
        
        if response["data"]["appPurchaseOneTimeCreate"]["userErrors"]:
            errors = response["data"]["appPurchaseOneTimeCreate"]["userErrors"]
            raise ShopifyBillingError(f"One-time charge creation failed: {errors}")
        
        return response["data"]["appPurchaseOneTimeCreate"]
    
    async def _make_graphql_request(self, shop_id: str, query: str, variables: Dict) -> Dict:
        """Make GraphQL request to Shopify"""
        url = f"https://{shop_id}/admin/api/2024-01/graphql.json"
        
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.api_key,  # Simplified for example
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()