# services/catalog-service/src/repositories/catalog_repository.py

from prisma import Prisma

from ..schemas.catalog import CatalogItemCreate, CatalogItemOut


class CatalogRepository:
    """Repository for catalog items using Prisma client"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def upsert(self, dto: CatalogItemCreate) -> CatalogItemOut:
        """Upsert catalog item"""
        item = await self.prisma.catalogitem.upsert(
            where={
                "merchant_id_platform_name_variant_id": {
                    "merchant_id": dto.merchant_id,
                    "platform_name": dto.platform_name,
                    "variant_id": dto.variant_id,
                }
            },
            update={
                "product_title": dto.product_title,
                "variant_title": dto.variant_title,
                "sku": dto.sku,
                "price": dto.price,
                "currency": dto.currency,
                "inventory_quantity": dto.inventory_quantity,
                "image_url": dto.image_url,
                "sync_status": "synced",
                "synced_at": dto.synced_at,
            },
            create={
                "merchant_id": dto.merchant_id,
                "platform_name": dto.platform_name,
                "platform_id": dto.platform_id,
                "platform_domain": dto.platform_domain,
                "product_id": dto.product_id,
                "variant_id": dto.variant_id,
                "image_id": dto.image_id,
                "product_title": dto.product_title,
                "variant_title": dto.variant_title,
                "sku": dto.sku,
                "price": dto.price,
                "currency": dto.currency,
                "inventory_quantity": dto.inventory_quantity,
                "image_url": dto.image_url,
                "sync_status": "synced",
                "platform_created_at": dto.platform_created_at,
                "platform_updated_at": dto.platform_updated_at,
            },
        )
        return CatalogItemOut.model_validate(item)

    async def find_by_id(self, item_id: str) -> CatalogItemOut | None:
        """Find catalog item by ID"""
        item = await self.prisma.catalogitem.find_unique(where={"id": item_id})
        return CatalogItemOut.model_validate(item) if item else None

    async def find_by_merchant(self, merchant_id: str, skip: int = 0, take: int = 100) -> list[CatalogItemOut]:
        """Find catalog items by merchant"""
        items = await self.prisma.catalogitem.find_many(
            where={"merchant_id": merchant_id},
            skip=skip,
            take=take,
            order_by={"created_at": "desc"},
        )
        return [CatalogItemOut.model_validate(item) for item in items]

    async def count_by_merchant(self, merchant_id: str) -> int:
        """Count catalog items for merchant"""
        return await self.prisma.catalogitem.count(where={"merchant_id": merchant_id})

    async def update_analysis_status(self, item_id: str, status: str) -> None:
        """Update analysis status"""
        await self.prisma.catalogitem.update(where={"id": item_id}, data={"analysis_status": status})
