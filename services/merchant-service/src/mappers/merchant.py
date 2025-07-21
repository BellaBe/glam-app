from ..models.merchant import Merchant
from ..schemas.merchant import MerchantIn, MerchantPatch, MerchantOut
from ..shared.mappers.crud import CRUDMapper


class MerchantMapper(CRUDMapper[Merchant, MerchantIn, MerchantPatch, MerchantOut]):
    """Concrete CRUD mapper – three lines, nothing more."""

    model_cls = Merchant
    out_schema = MerchantOut