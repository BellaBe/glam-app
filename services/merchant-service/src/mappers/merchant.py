# services/merchant-service/src/mappers/merchant_mapper.py
from shared.mappers.crud_mapper import CRUDMapper
from ..models.merchant import Merchant
from ..schemas.merchant import MerchantBootstrap, MerchantUpdate, MerchantResponse

class MerchantMapper(CRUDMapper[Merchant, MerchantBootstrap, MerchantUpdate, MerchantResponse]):
    """CRUD mapper for Merchant"""
    model_cls = Merchant
    out_schema = MerchantResponse
    
    def to_model(self, dto: MerchantBootstrap, **extra) -> Merchant:
        """Custom conversion if needed"""
        return super().to_model(dto, **extra)
