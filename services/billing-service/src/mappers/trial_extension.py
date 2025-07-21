# services/billing-service/src/mappers/trial_extension_mapper.py
"""Mapper for trial extension model to response schemas."""

from ..models import TrialExtension
from ..schemas.trial_extension import TrialExtensionIn, TrialExtensionOut, TrialExtensionPatch
from shared.mappers.crud_mapper import CRUDMapper

class TrialExtensionMapper(
    CRUDMapper[TrialExtension, TrialExtensionIn, TrialExtensionPatch, TrialExtensionOut]
):
    model_cls  = TrialExtension
    out_schema = TrialExtensionOut
