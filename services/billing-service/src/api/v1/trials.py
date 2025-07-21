# services/billing-service/src/api/v1/trials.py
from datetime import datetime
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Body,
    status,
)

from shared.api import ApiResponse, success_response, RequestContextDep
from ...services import TrialService
from ...schemas.trial_extension import (
    TrialExtensionIn,
    TrialExtensionOut,
    TrialStatusOut,
)
from ...exceptions import ConflictError

router = APIRouter(prefix="/trials", tags=["Trials"])

@router.get(
    "/{merchant_id}",
    response_model=ApiResponse[TrialStatusOut],
    status_code=status.HTTP_200_OK,
    summary="Get current trial status",
)
async def get_trial_status(
    svc: TrialService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(..., description="Merchant UUID"),
):
    """
    Returns start date, end date, days remaining, and extension stats for a merchant’s trial.
    """
    status_out = await svc.get_trial_status(merchant_id)
    return success_response(
        data=status_out,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )

@router.post(
    "/{merchant_id}/extend",
    response_model=ApiResponse[TrialExtensionOut],
    status_code=status.HTTP_201_CREATED,
    summary="Extend a merchant's trial (admin only)",
)
async def extend_trial(
    svc: TrialService,
    ctx: RequestContextDep,
    merchant_id: UUID = Path(..., description="Merchant UUID"),
    body: TrialExtensionIn = Body(..., description="Extension payload"),
):
    """
    Adds `additional_days` to the merchant’s trial period.
    """
    try:
        out = await svc.extend_trial(
            merchant_id=merchant_id,
            additional_days=body.additional_days,
            reason=body.reason,
            extended_by=body.extended_by,
        )
        return success_response(
            data=out,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
        )
    except ConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))
