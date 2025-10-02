# shared/utils/idempotency.py
"""Simple idempotency key generator."""

from uuid import UUID


def generate_idempotency_key(
    system: str, operation_type: str, identifier: str | int | UUID, extra: str | None = None
) -> str:
    """
    Generate idempotency key: SYSTEM_OPERATION_ID[_EXTRA]

    Examples:
        generate_idempotency_key("SHOPIFY", "ORDER", "123456")
        → "SHOPIFY_ORDER_123456"

        generate_idempotency_key("STRIPE", "PAYMENT", "pi_abc123")
        → "STRIPE_PAYMENT_pi_abc123"

        generate_idempotency_key("SHOPIFY", "ORDER", "123", "TESTSTORE")
        → "SHOPIFY_ORDER_123_TESTSTORE"
    """
    # Normalize inputs
    system = str(system).upper().replace("-", "_").replace(".", "_")
    operation_type = str(operation_type).upper().replace("-", "_").replace(".", "_")
    identifier = str(identifier)

    # Build key
    parts = [system, operation_type, identifier]

    if extra:
        parts.append(str(extra).upper().replace("-", "_").replace(".", "_"))

    return "_".join(parts)
