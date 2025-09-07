# services/platform-connector/src/adapters/shopify.py (updated)
import asyncio
from collections.abc import AsyncIterator
from typing import Any

import aiohttp

from shared.utils.exceptions import InfrastructureError, RequestTimeoutError, UnauthorizedError

from ..services.token_service import TokenServiceClient
from .base import PlatformAdapter


class ShopifyAdapter(PlatformAdapter):
    """Shopify platform adapter using GraphQL API with Token Service"""

    def __init__(self, logger, config, token_client: TokenServiceClient):
        super().__init__(logger, config)
        self.token_client = token_client

    PRODUCTS_QUERY = """
    query getProducts($cursor: String) {
        products(first: 250, after: $cursor) {
            edges {
                node {
                    id
                    title
                    createdAt
                    updatedAt
                    variants(first: 100) {
                        edges {
                            node {
                                id
                                title
                                sku
                                price
                                inventoryQuantity
                                image {
                                    url
                                }
                            }
                        }
                    }
                    featuredImage {
                        url
                    }
                }
                cursor
            }
            pageInfo {
                hasNextPage
            }
        }
    }
    """

    async def authenticate(self, credentials: dict[str, Any]) -> str:
        """Get access token from Token Service"""
        domain = credentials.get("domain")
        correlation_id = credentials.get("correlation_id", "unknown")

        if not domain:
            raise ValueError("domain required for Shopify authentication")

        try:
            # Get token from Token Service
            token = await self.token_client.get_shopify_token(domain=domain, correlation_id=correlation_id)

            return token

        except NotFoundError:
            # Token not found in Token Service
            raise UnauthorizedError(
                f"No Shopify access token found for shop: {domain}",
                auth_type="shopify_oauth",
                details={"domain": domain},
            )
        except InfrastructureError as e:
            # Token Service unavailable
            self.logger.exception(f"Token Service error: {e}", extra={"domain": domain})
            raise

    async def fetch_products(
        self, merchant_id: str, platform_shop_id: str, domain: str, sync_id: str, correlation_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Fetch products from Shopify in batches"""

        # Get access token from Token Service
        token = await self.authenticate({"domain": domain, "correlation_id": correlation_id})

        if not token:
            raise UnauthorizedError(f"Failed to get Shopify token for {domain}", auth_type="shopify_oauth")

        self.logger.info(
            f"Starting Shopify product fetch for {domain}",
            extra={"correlation_id": correlation_id, "sync_id": sync_id, "merchant_id": merchant_id},
        )

        batch_num = 0
        cursor = None
        total_products = 0

        async with aiohttp.ClientSession() as session:
            while True:
                batch_num += 1

                try:
                    # Execute GraphQL query
                    response_data = await self._execute_graphql(
                        session, domain, token, self.PRODUCTS_QUERY, {"cursor": cursor}
                    )

                    # Transform products
                    products_batch = []
                    for edge in response_data["data"]["products"]["edges"]:
                        product = edge["node"]

                        # Process each variant
                        for variant_edge in product.get("variants", {}).get("edges", []):
                            variant = variant_edge["node"]

                            transformed = self.transform_product(
                                {
                                    "product": product,
                                    "variant": variant,
                                    "domain": domain,
                                    "platform_shop_id": platform_shop_id,
                                }
                            )

                            products_batch.append(transformed)

                    total_products += len(products_batch)

                    # Check if there are more pages
                    has_more = response_data["data"]["products"]["pageInfo"]["hasNextPage"]

                    # Yield this batch
                    yield {
                        "merchant_id": merchant_id,
                        "sync_id": sync_id,
                        "platform_name": "shopify",
                        "platform_shop_id": platform_shop_id,
                        "domain": domain,
                        "products": products_batch,
                        "batch_num": batch_num,
                        "has_more": has_more,
                    }

                    if not has_more:
                        break

                    # Get cursor for next page
                    edges = response_data["data"]["products"]["edges"]
                    if edges:
                        cursor = edges[-1]["cursor"]

                    # Rate limit protection
                    await asyncio.sleep(self.config.get("shopify_rate_limit_delay", 0.5))

                except UnauthorizedError:
                    # Token might be expired or revoked
                    self.logger.exception(
                        f"Shopify authentication failed for {domain}",
                        extra={"correlation_id": correlation_id, "sync_id": sync_id},
                    )
                    raise

                except aiohttp.ClientError as e:
                    raise InfrastructureError(
                        f"Failed to fetch products from Shopify: {e}", service="shopify_api", retryable=True
                    )

                except TimeoutError:
                    raise RequestTimeoutError(
                        "Shopify API request timed out", timeout_seconds=30, operation="fetch_products"
                    )

        self.logger.info(
            "Completed Shopify product fetch",
            extra={
                "correlation_id": correlation_id,
                "sync_id": sync_id,
                "total_products": total_products,
                "batches": batch_num,
            },
        )

    async def _execute_graphql(
        self, session: aiohttp.ClientSession, domain: str, token: str, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute GraphQL query against Shopify Admin API"""

        url = f"https://{domain}/admin/api/2024-01/graphql.json"
        headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

        payload = {"query": query, "variables": variables}

        async with session.post(
            url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 401:
                raise UnauthorizedError("Invalid Shopify access token", auth_type="shopify_oauth")

            if response.status == 429:
                # Rate limited
                retry_after = response.headers.get("Retry-After", "5")
                raise InfrastructureError(
                    "Shopify rate limit exceeded",
                    service="shopify_api",
                    retryable=True,
                    details={"retry_after": retry_after},
                )

            response.raise_for_status()
            return await response.json()

    def transform_product(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform Shopify product to internal format"""
        product = raw_data["product"]
        variant = raw_data["variant"]

        # Get image URL (variant image or product featured image)
        image_url = None
        if variant.get("image", {}).get("url"):
            image_url = variant["image"]["url"]
        elif product.get("featuredImage", {}).get("url"):
            image_url = product["featuredImage"]["url"]

        return {
            "platform_name": "shopify",
            "platform_shop_id": raw_data["platform_shop_id"],
            "domain": raw_data["domain"],
            "product_id": self.extract_id(product["id"]),
            "variant_id": self.extract_id(variant["id"]),
            "product_title": product["title"],
            "variant_title": variant.get("title") or product["title"],
            "sku": variant.get("sku"),
            "price": float(variant.get("price", 0)),
            "currency": "USD",  # Shopify default
            "inventory": variant.get("inventoryQuantity", 0),
            "image_url": image_url,
            "created_at": product.get("createdAt"),
            "updated_at": product.get("updatedAt"),
        }
