# services/credit-service/src/api/v1/transactions.py
"""Credit transaction API endpoints."""

from uuid import UUID
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.security import HTTPBearer

from shared.api import (
    ApiResponse,
    success_response,
    paginated_response,
    RequestContextDep,
    PaginationDep,
)

from ...dependencies import (
    CreditTransactionServiceDep,
)
from ...schemas.credit_transaction import (
    CreditTransactionResponse, 
    CreditTransactionListResponse,
    TransactionStatsByMerchantIdResponse,
)
from ...models.credit_transaction import TransactionType, OperationType

router = APIRouter(prefix="/transactions", tags=["transactions"])
security = HTTPBearer()


@router.get("/{transaction_id}", 
            response_model=ApiResponse[CreditTransactionResponse], 
            tags=["transactions"], 
            status_code=status.HTTP_200_OK,
            summary="Get specific credit transaction by ID")
async def get_transaction(
    transaction_id: UUID,
    transaction_service: CreditTransactionServiceDep,
    ctx: RequestContextDep
):
    """Get specific credit transaction by ID"""
    
    transaction = await transaction_service.get_transaction_by_id(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found."
        )
    
    return success_response(
        data=transaction,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )


@router.get("/merchant/{merchant_id}", 
            response_model=ApiResponse[CreditTransactionListResponse], 
            tags=["transactions"], 
            status_code=status.HTTP_200_OK,
            summary="List credit transactions for a merchant with pagination and filtering")
async def list_transactions_by_merchant_id(
    merchant_id: UUID,
    svc: CreditTransactionServiceDep,
    pagination: PaginationDep,
    ctx: RequestContextDep,
    operation_type: Optional[OperationType] = Query(None, description="Filter by operation type"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
):
    """Get credit transactions with pagination and filtering"""
    
    # Get transactions with filtering
    total, transactions = await svc.list_transactions_by_merchant_id(
        merchant_id=merchant_id,
        limit=pagination.limit,
        offset=pagination.offset,
        operation_type=operation_type,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transactions found for merchant {merchant_id} with the specified filters."
        )
    
    
    return paginated_response(
        data=transactions,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        base_url="/api/v1/transactions",
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id,
    )
        
        
@router.get("/merchant/{merchant_id}/stats", 
            response_model=ApiResponse[TransactionStatsByMerchantIdResponse], tags=["transactions"], 
            status_code=status.HTTP_200_OK)
async def get_merchant_transaction_stats(
    merchant_id: UUID,
    svc: CreditTransactionServiceDep,
    ctx: RequestContextDep,

):
    """Get transaction statistics for a merchant"""
    
    stats = await svc.get_merchant_stats(merchant_id=merchant_id)
    
    return success_response(
        data=stats,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )

# Admin endpoints
@router.post("/admin/manual-adjustment", 
            response_model=ApiResponse[dict], 
            tags=["admin"],
            status_code=status.HTTP_201_CREATED,
            summary="[ADMIN] Create manual credit adjustment")
async def create_manual_adjustment(
    merchant_id: UUID,
    operation_type: OperationType,
    credits_to_use: int,
    reason: str,
    admin_id: str,
    svc: CreditTransactionServiceDep,
    ctx: RequestContextDep,
):
    """
    [ADMIN ONLY] Create a manual credit adjustment for a merchant.
    
    This endpoint allows administrators to manually increase or decrease
    a merchant's credit balance with proper audit trail.
    """

    
    transaction = await svc.process_manual_adjustment(
        merchant_id=merchant_id,
        operation_type=operation_type,
        credits_to_use=credits_to_use,
        reason=reason,
        admin_id=admin_id
    )
    
    return success_response(
        data=transaction,
        request_id=ctx.request_id,
        correlation_id=ctx.correlation_id
    )
