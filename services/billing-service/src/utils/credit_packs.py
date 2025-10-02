from ..config import ServiceConfig
from ..schemas.billing import CreditPack


class CreditPackManager:
    """Manages credit pack configurations"""

    def __init__(self, config: ServiceConfig):
        self.packs = {
            CreditPack.SMALL: {"credits": config.small_pack_credits, "price": config.small_pack_price},
            CreditPack.MEDIUM: {"credits": config.medium_pack_credits, "price": config.medium_pack_price},
            CreditPack.LARGE: {"credits": config.large_pack_credits, "price": config.large_pack_price},
        }

    def get_pack(self, pack_type: CreditPack) -> dict | None:
        """Get pack configuration"""
        return self.packs.get(pack_type)

    def get_credits(self, pack_type: CreditPack) -> int:
        """Get credits for pack"""
        pack = self.get_pack(pack_type)
        return pack["credits"] if pack else 0

    def get_price(self, pack_type: CreditPack) -> str:
        """Get price for pack"""
        pack = self.get_pack(pack_type)
        return pack["price"] if pack else "0.00"
