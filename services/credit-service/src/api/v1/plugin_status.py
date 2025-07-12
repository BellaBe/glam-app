# services/credit-service/src/api/v1/plugin_status.py
"""Plugin status API endpoints."""

from uuid import UUID
from fastapi import APIRouter

from shared.api.responses import success_response

from shared.api import (
    ApiResponse,
    success_response,
    RequestContextDep,
)

from ...dependencies import PluginStatusServiceDep
from ...schemas.plugin_status import PluginStatusResponse

router = APIRouter(prefix="/plugin-status", tags=["plugin-status"])


@router.get("/{merchant_id}", response_model=ApiResponse[PluginStatusResponse], summary="Get plugin status for merchant")
async def get_plugin_status(
    merchant_id: UUID,
    svc: PluginStatusServiceDep,
    ctx: RequestContextDep
):
    """
    Get plugin status for merchant.
    Returns whether the plugin/widget is enabled or disabled based on credit balance.
    Always returns 200 OK with status information.
    """
    
    status = await svc.get_plugin_status(merchant_id)
    
    return success_response(
        data=status,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )
        
            
        
        