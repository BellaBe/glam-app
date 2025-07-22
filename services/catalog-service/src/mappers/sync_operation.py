# src/mappers/sync_operation_mapper.py
from shared.mappers.crud import CRUDMapper
from ..models.sync_operation import SyncOperation
from ..schemas.sync import SyncOperationIn, SyncOperationOut
from pydantic import BaseModel

class SyncOperationPatch(BaseModel):
    """Patch DTO for sync operations"""
    status: Optional[str] = None
    total_products: Optional[int] = None
    processed_products: Optional[int] = None
    failed_products: Optional[int] = None
    images_cached: Optional[int] = None
    analysis_requested: Optional[int] = None
    analysis_completed: Optional[int] = None
    bulk_operation_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SyncOperationMapper(CRUDMapper[SyncOperation, SyncOperationIn, SyncOperationPatch, SyncOperationOut]):
    """CRUD mapper for SyncOperation"""
    model_cls = SyncOperation
    out_schema = SyncOperationOut