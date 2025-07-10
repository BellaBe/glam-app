# services/credit-service/src/api/v1/plugin_status.py
"""Plugin status API endpoints."""

from uuid import UUID
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from shared.api.responses import success_response
from shared.errors import NotFoundError, DomainError

from ...dependencies import PluginStatusServiceDep
from ...schemas.plugin_status import PluginStatusResponse

router = APIRouter(prefix="/plugin-status", tags=["plugin-status"])


@router.get("/{merchant_id}")
async def get_plugin_status(
    merchant_id: UUID,
    plugin_status_service: PluginStatusServiceDep
) -> JSONResponse:
    """
    Get plugin status for merchant.
    
    Returns whether the plugin/widget is enabled or disabled based on credit balance.
    Always returns 200 OK with status information.
    """
    try:
        status = await plugin_status_service.get_plugin_status(merchant_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": status.status,
                "reason": status.reason,
                "balance": float(status.balance),
                "account_status": status.account_status
            }
        )
        
    except NotFoundError:
        # For plugin status, we return disabled if merchant not found
        return JSONResponse(
            status_code=200,
            content={
                "status": "disabled",
                "reason": "Merchant not found",
                "balance": 0,
                "account_status": "not_found"
            }
        )
        
    except Exception as e:
        # Return disabled status on any error to avoid breaking plugins
        return JSONResponse(
            status_code=200,
            content={
                "status": "disabled",
                "reason": "Service error",
                "balance": 0,
                "account_status": "error"
            }
        )