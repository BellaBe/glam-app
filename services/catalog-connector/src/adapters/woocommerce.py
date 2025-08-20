# services/platform-connector/src/adapters/woocommerce.py (updated)
import asyncio
import aiohttp
from typing import AsyncIterator, Dict, Any
from base64 import b64encode

from shared.utils.exceptions import InfrastructureError, UnauthorizedError, NotFoundError

from .base import PlatformAdapter
from ..services.token_service import TokenServiceClient

class WooCommerceAdapter(PlatformAdapter):
    """WooCommerce platform adapter with Token Service integration"""
    
    def __init__(self, logger, config, token_client: TokenServiceClient):
        super().__init__(logger, config)
        self.token_client = token_client
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers from Token Service"""
        domain = credentials.get("domain")
        correlation_id = credentials.get("correlation_id", "unknown")
        
        if not domain:
            raise ValueError("domain required for WooCommerce authentication")
        
        try:
            # Get credentials from Token Service
            creds = await self.token_client.get_woocommerce_credentials(
                domain=domain,
                correlation_id=correlation_id
            )
            
            # Create Basic auth header
            auth_string = f"{creds['consumer_key']}:{creds['consumer_secret']}"
            encoded = b64encode(auth_string.encode()).decode()
            
            return {
                "Authorization": f"Basic {encoded}"
            }
            
        except NotFoundError:
            raise UnauthorizedError(
                f"No WooCommerce credentials found for: {domain}",
                auth_type="woocommerce_api",
                details={"domain": domain}
            )
        except InfrastructureError as e:
            self.logger.error(
                f"Token Service error: {e}",
                extra={"domain": domain}
            )
            raise
    
    async def fetch_products(
        self,
        merchant_id: str,
        platform_shop_id: str,
        shop_domain: str,
        sync_id: str,
        correlation_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch products from WooCommerce in batches"""
        
        # Get auth headers from Token Service
        headers = await self.authenticate({
            "domain": shop_domain,
            "correlation_id": correlation_id
        })
        
        self.logger.info(
            f"Starting WooCommerce product fetch for {shop_domain}",
            extra={
                "correlation_id": correlation_id,
                "sync_id": sync_id,
                "merchant_id": merchant_id
            }
        )
        
        batch_num = 0
        page = 1
        total_products = 0
        per_page = self.config.get("woocommerce_batch_size", 100)
        
        async with aiohttp.ClientSession() as session:
            while True:
                batch_num += 1
                
                # Fetch products page
                url = f"https://{shop_domain}/wp-json/wc/v3/products"
                params = {
                    "page": page,
                    "per_page": per_page,
                    "status": "publish"
                }
                
                try:
                    async with session.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 401:
                            raise UnauthorizedError(
                                f"Invalid WooCommerce credentials for {shop_domain}",
                                auth_type="woocommerce_api"
                            )
                        
                        response.raise_for_status()
                        products = await response.json()
                        
                        # Transform products
                        products_batch = []
                        for product in products:
                            # Handle variations
                            if product.get("variations"):
                                for var_id in product["variations"]:
                                    variation = await self._fetch_variation(
                                        session, shop_domain, product["id"], var_id, headers
                                    )
                                    transformed = self.transform_product({
                                        "product": product,
                                        "variation": variation,
                                        "shop_domain": shop_domain,
                                        "platform_shop_id": platform_shop_id
                                    })
                                    products_batch.append(transformed)
                            else:
                                # Simple product
                                transformed = self.transform_product({
                                    "product": product,
                                    "variation": None,
                                    "shop_domain": shop_domain,
                                    "platform_shop_id": platform_shop_id
                                })
                                products_batch.append(transformed)
                        
                        total_products += len(products_batch)
                        
                        # Check if more pages
                        total_pages = int(response.headers.get("X-WP-TotalPages", 1))
                        has_more = page < total_pages
                        
                        # Yield batch
                        yield {
                            "merchant_id": merchant_id,
                            "sync_id": sync_id,
                            "platform_name": "woocommerce",
                            "platform_shop_id": platform_shop_id,
                            "shop_domain": shop_domain,
                            "products": products_batch,
                            "batch_num": batch_num,
                            "has_more": has_more
                        }
                        
                        if not has_more:
                            break
                        
                        page += 1
                        
                        # Rate limit protection
                        await asyncio.sleep(0.2)
                        
                except aiohttp.ClientError as e:
                    raise InfrastructureError(
                        f"Failed to fetch products from WooCommerce: {e}",
                        service="woocommerce_api",
                        retryable=True
                    )
        
        self.logger.info(
            f"Completed WooCommerce product fetch",
            extra={
                "correlation_id": correlation_id,
                "sync_id": sync_id,
                "total_products": total_products,
                "batches": batch_num
            }
        )
    
    async def _fetch_variation(
        self,
        session: aiohttp.ClientSession,
        domain: str,
        product_id: int,
        variation_id: int,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Fetch single variation details"""
        url = f"https://{domain}/wp-json/wc/v3/products/{product_id}/variations/{variation_id}"
        
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    def transform_product(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform WooCommerce product to internal format"""
        product = raw_data["product"]
        variation = raw_data.get("variation")
        
        if variation:
            # Use variation data
            variant_id = str(variation["id"])
            variant_title = variation.get("name") or product["name"]
            sku = variation.get("sku") or product.get("sku")
            price = float(variation.get("price", 0))
            stock = variation.get("stock_quantity", 0)
            image_url = variation["image"]["src"] if variation.get("image") else None
        else:
            # Simple product
            variant_id = f"{product['id']}_default"
            variant_title = product["name"]
            sku = product.get("sku")
            price = float(product.get("price", 0))
            stock = product.get("stock_quantity", 0)
            image_url = product["images"][0]["src"] if product.get("images") else None
        
        return {
            "platform_name": "woocommerce",
            "platform_shop_id": raw_data["platform_shop_id"],
            "shop_domain": raw_data["shop_domain"],
            "product_id": str(product["id"]),
            "variant_id": variant_id,
            "product_title": product["name"],
            "variant_title": variant_title,
            "sku": sku,
            "price": price,
            "currency": "USD",
            "inventory": stock,
            "image_url": image_url,
            "created_at": product.get("date_created"),
            "updated_at": product.get("date_modified")
        }