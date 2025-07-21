# services/billing-service/src/schemas/trial_extension.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from ..models.enums import TrialExtensionReason

# ---------- IN ----------
class TrialExtensionIn(BaseModel):
    merchant_id: UUID
    additional_days: int = Field(..., ge=1, le=30)
    reason: TrialExtensionReason
    extended_by: str = Field(..., max_length=255)

    model_config = ConfigDict(extra="forbid")

# ---------- OUT ----------
class TrialExtensionOut(BaseModel):
    id: UUID
    merchant_id: UUID
    days_added: int
    reason: TrialExtensionReason
    extended_by: str
    original_trial_end: datetime
    new_trial_end: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ---------- STATUS ----------
class TrialStatusOut(BaseModel):
    merchant_id: UUID
    is_trial_active: bool
    trial_start_date: datetime
    trial_end_date: datetime
    days_remaining: int
    total_extensions: int
    total_extension_days: int
