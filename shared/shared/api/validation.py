# shared/api/validation.py
from fastapi import HTTPException, status

from shared.api.dependencies import InternalAuthContext
from shared.utils.logger import ServiceLogger


def ensure_allowed_service(
    auth: InternalAuthContext, allowed: list[str], *, operation: str, logger: ServiceLogger
) -> None:
    if auth.service not in allowed:
        logger.warning("unauthorized_internal_service", extra={"service": auth.service, "operation": operation})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "SERVICE_NOT_ALLOWED",
                "message": f"Service '{auth.service}' not allowed for '{operation}'",
            },
        )
