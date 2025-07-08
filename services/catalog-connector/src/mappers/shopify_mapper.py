# File: services/connector-service/src/mappers/shopify_mapper.py

"""Mapper for transforming Shopify data to internal format."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import html
import re

from ..schemas.catalog import CatalogItem, CatalogVariant, CatalogImage


class ShopifyMapper:
    """Maps Shopify API data to internal catalog format."""
    
    @staticmethod
    def _sanitize_html(html_content: Optional[str]) -> Optional[str]:
        """Sanitize HTML content."""
        if not html_content:
            return None
            
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities
        text = html.unescape(text)
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip() if text else None
    
    @staticmethod
    def _parse_tags(tags: Optional[str]) -> List[str]:
        """Parse comma-separated tags."""
        if not tags:
            return []
        return [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    @classmethod
    def map_product_to_catalog_item(cls, product: Dict[str, Any]) -> CatalogItem:
        """Map Shopify product to catalog item."""
        return CatalogItem(
            external_id=str(product["id"]),
            title=product["title"],
            description=cls._sanitize_html(product.get("body_html")),
            vendor=product.get("vendor"),
            product_type=product.get("product_type"),
            tags=cls._parse_tags(product.get("tags")),
            status=product.get("status", "active"),
            external_created_at=datetime.fromisoformat(
                product["created_at"].replace("Z", "+00:00")
            ),
            external_updated_at=datetime.fromisoformat(
                product["updated_at"].replace("Z", "+00:00")
            ),
            variants=cls._map_variants(product.get("variants", [])),
            images=cls._map_images(product.get("images", [])),
            metadata={
                "handle": product.get("handle"),
                "published_at": product.get("published_at"),
                "template_suffix": product.get("template_suffix"),
            }
        )
    
    @classmethod
    def _map_variants(cls, variants: List[Dict[str, Any]]) -> List[CatalogVariant]:
        """Map Shopify variants to catalog variants."""
        return [
            CatalogVariant(
                external_id=str(variant["id"]),
                title=variant.get("title", ""),
                sku=variant.get("sku"),
                price=variant.get("price", "0"),
                inventory_quantity=variant.get("inventory_quantity", 0),
                options={
                    "option1": variant.get("option1"),
                    "option2": variant.get("option2"),
                    "option3": variant.get("option3"),
                }
            )
            for variant in variants
        ]
    
    @classmethod
    def _map_images(cls, images: List[Dict[str, Any]]) -> List[CatalogImage]:
        """Map Shopify images to catalog images."""
        return [
            CatalogImage(
                external_id=str(image["id"]),
                url=image["src"],
                alt_text=image.get("alt"),
                position=image.get("position", 0)
            )
            for image in images
        ]
    
    @classmethod
    def map_products_batch(cls, products: List[Dict[str, Any]]) -> List[CatalogItem]:
        """Map batch of Shopify products."""
        return [cls.map_product_to_catalog_item(product) for product in products]