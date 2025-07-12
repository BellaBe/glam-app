# services/credit-service/src/utils/credit_calculations.py
"""Utilities for credit calculations."""

from typing import Union


def calculate_order_credits(
    order_total: int,
    fixed_amount: Decimal,
    percentage: Decimal,
    minimum: Decimal
) -> Decimal:
    """
    Calculate credits for an order based on configuration.
    
    Args:
        order_total: Total order amount
        fixed_amount: Fixed credit amount per order
        percentage: Percentage of order total to give as credits
        minimum: Minimum credits to award
    
    Returns:
        Credit amount to award
    """
    # Calculate percentage-based credits
    percentage_credits = order_total * percentage
    
    # Use the higher of fixed amount or percentage
    credits = max(fixed_amount, percentage_credits)
    
    # Ensure minimum
    credits = max(credits, minimum)
    
    # Round to 2 decimal places
    return credits.quantize(Decimal('0.01'))


def calculate_refund_credits(
    original_credits: Decimal,
    refund_amount: Decimal,
    original_order_total: Decimal
) -> Decimal:
    """
    Calculate credits to refund based on refund amount.
    
    Args:
        original_credits: Credits originally awarded
        refund_amount: Amount being refunded
        original_order_total: Original order total
    
    Returns:
        Credits to refund (proportional to refund amount)
    """
    if original_order_total == 0:
        return Decimal("0.00")
    
    # Calculate proportional refund
    refund_ratio = refund_amount / original_order_total
    
    # Apply ratio to original credits
    refund_credits = original_credits * refund_ratio
    
    # Ensure we don't refund more than originally awarded
    refund_credits = min(refund_credits, original_credits)
    
    # Round to 2 decimal places
    return refund_credits.quantize(Decimal('0.01'))


def calculate_low_balance_threshold(
    trial_credits: Decimal,
    threshold_percentage: int
) -> Decimal:
    """
    Calculate low balance threshold.
    
    Args:
        trial_credits: Initial trial credits amount
        threshold_percentage: Percentage threshold (e.g., 20 for 20%)
    
    Returns:
        Low balance threshold amount
    """
    threshold = trial_credits * Decimal(str(threshold_percentage / 100))
    return threshold.quantize(Decimal('0.01'))


def format_credit_amount(amount: Union[Decimal, float]) -> str:
    """
    Format credit amount for display.
    
    Args:
        amount: Credit amount
    
    Returns:
        Formatted string
    """
    if isinstance(amount, float):
        amount = Decimal(str(amount))
    
    # Format with 2 decimal places, no trailing zeros
    formatted = f"{amount:.2f}".rstrip('0').rstrip('.')
    
    return formatted


def validate_credit_amount(amount: Union[Decimal, float, str]) -> Decimal:
    """
    Validate and convert credit amount to Decimal.
    
    Args:
        amount: Amount to validate
    
    Returns:
        Validated Decimal amount
    
    Raises:
        ValueError: If amount is invalid
    """
    try:
        if isinstance(amount, str):
            decimal_amount = Decimal(amount)
        elif isinstance(amount, float):
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            decimal_amount = amount
        else:
            raise ValueError(f"Invalid amount type: {type(amount)}")
        
        # Validate positive
        if decimal_amount < 0:
            raise ValueError("Amount cannot be negative")
        
        # Validate precision (max 2 decimal places)
        if decimal_amount.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        
        return decimal_amount.quantize(Decimal('0.01'))
        
    except (ValueError, TypeError, ArithmeticError) as e:
        raise ValueError(f"Invalid credit amount: {amount}") from e