from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models.merchant import Merchant
from ..shared.database.repository import Repository


class MerchantRepository(Repository[Merchant]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(Merchant, session_factory)

    # ------ extra domain‑specific queries (copied from original) ------ #

    async def find_by_shop_id(self, shop_id: str) -> Merchant | None:  # noqa: D401
        """Get merchant by Shopify shop ID (unchanged)."""
        async for session in self._session():
            result = await session.execute(
                select(Merchant).where(Merchant.shop_id == shop_id)
            )
            return result.scalar_one_or_none()
        return None