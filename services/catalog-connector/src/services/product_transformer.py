# src/services/product_transformer.py
import json
from datetime import datetime
from typing import Any

from shared.utils.logger import ServiceLogger

from ..schemas.product import ProductVariantOut


class ProductTransformer:
    """Transform Shopify product data to internal format"""

    def __init__(self, logger: ServiceLogger):
        self.logger = logger

    def transform_shopify_products(self, jsonl_data: str, shop_id: str) -> list[ProductVariantOut]:
        """Transform JSONL data from Shopify bulk operation"""
        products = []
        current_product = None

        for line_num, line in enumerate(jsonl_data.strip().split("\n")):
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                if data.get("__typename") == "Product":
                    current_product = self._parse_product_data(data)
                elif data.get("__typename") == "ProductVariant" and current_product:
                    variant = self._parse_variant_data(data, current_product)
                    if variant:
                        products.append(variant)
                elif data.get("__typename") == "Image":
                    # Images are handled within product/variant context
                    continue

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON at line {line_num + 1}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Failed to transform product at line {line_num + 1}: {e}")
                continue

        self.logger.info(f"Transformed {len(products)} product variants from JSONL")
        return products

    def _parse_product_data(self, product_data: dict[str, Any]) -> dict[str, Any]:
        """Parse product-level data"""
        return {
            "id": self._extract_id(product_data.get("id", "")),
            "title": product_data.get("title"),
            "description": product_data.get("description"),
            "vendor": product_data.get("vendor"),
            "productType": product_data.get("productType"),
            "tags": product_data.get("tags", []),
            "createdAt": self._parse_timestamp(product_data.get("createdAt")),
            "updatedAt": self._parse_timestamp(product_data.get("updatedAt")),
            "images": product_data.get("images", {}).get("edges", []),
        }

    def _parse_variant_data(
        self, variant_data: dict[str, Any], product_data: dict[str, Any]
    ) -> ProductVariantOut | None:
        """Parse variant-level data and combine with product data"""
        try:
            variant_id = self._extract_id(variant_data.get("id", ""))
            if not variant_id:
                return None

            # Find variant image
            image_url = None
            image_id = None

            if variant_data.get("image"):
                image_url = variant_data["image"].get("url")
                image_id = self._extract_id(variant_data["image"].get("id", ""))
            elif product_data.get("images"):
                # Use first product image if no variant-specific image
                first_image = product_data["images"][0]["node"]
                image_url = first_image.get("url")
                image_id = self._extract_id(first_image.get("id", ""))

            # Parse variant options
            variant_options = {}
            selected_options = variant_data.get("selectedOptions", [])
            for option in selected_options:
                variant_options[option.get("name", "")] = option.get("value", "")

            return ProductVariantOut(
                product_id=product_data["id"],
                variant_id=variant_id,
                image_id=image_id,
                # Product data
                title=product_data.get("title"),
                description=product_data.get("description"),
                vendor=product_data.get("vendor"),
                product_type=product_data.get("productType"),
                tags=product_data.get("tags", []),
                # Variant data
                variant_title=variant_data.get("title"),
                sku=variant_data.get("sku"),
                price=float(variant_data.get("price", "0") or "0"),
                inventory_quantity=int(variant_data.get("inventoryQuantity", 0) or 0),
                variant_options=variant_options,
                # Image
                image_url=image_url,
                # Timestamps
                shopify_created_at=product_data.get("createdAt"),
                shopify_updated_at=product_data.get("updatedAt"),
            )

        except Exception as e:
            self.logger.error(f"Failed to parse variant data: {e}")
            return None

    def _extract_id(self, gid: str) -> str:
        """Extract numeric ID from Shopify GID"""
        if not gid:
            return ""

        if "/" in gid:
            return gid.split("/")[-1]
        return gid

    def _parse_timestamp(self, timestamp_str: str | None) -> datetime | None:
        """Parse ISO timestamp string"""
        if not timestamp_str:
            return None

        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            return None
