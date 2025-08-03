# shared/database/helpers.py
"""Common query helpers for Prisma operations."""
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from uuid import UUID


def shop_filter(
    shop_id: Optional[Union[str, UUID]] = None,
    shop_domain: Optional[str] = None,
    field_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate filter for shop/merchant queries.
    
    Args:
        shop_id: Shop/merchant UUID
        shop_domain: Shop domain (e.g., "example.myshopify.com")
        field_prefix: Field prefix for nested relations (e.g., "merchant" -> "merchantId")
        
    Returns:
        Filter dictionary for Prisma where clause
        
    Example:
        # Filter by shop_id
        products = await db.product.find_many(
            where=shop_filter(shop_id="123e4567-e89b-12d3-a456-426614174000")
        )
        
        # Filter by domain
        products = await db.product.find_many(
            where=shop_filter(shop_domain="example.myshopify.com")
        )
        
        # Filter nested relation
        orders = await db.order.find_many(
            where=shop_filter(
                shop_id=shop_id,
                field_prefix="merchant"
            )
        )
        # This generates: {"merchantId": shop_id}
    """
    if not shop_id and not shop_domain:
        return {}
    
    # Determine field names
    id_field = f"{field_prefix}Id" if field_prefix else "shopId"
    domain_field = f"{field_prefix}Domain" if field_prefix else "shopDomain"
    
    # Alternative common field names
    if field_prefix:
        # Already has prefix, use it as is
        pass
    else:
        # Try to auto-detect common field names
        # You can customize this based on your schema conventions
        id_field_alternatives = ["shopId", "merchantId"]
        domain_field_alternatives = ["shopDomain", "merchantDomain"]
    
    filters = {}
    
    if shop_id:
        filters[id_field] = str(shop_id)
    
    if shop_domain:
        filters[domain_field] = shop_domain
    
    # If both are provided, use AND logic
    if shop_id and shop_domain:
        return {"AND": [
            {id_field: str(shop_id)},
            {domain_field: shop_domain}
        ]}
    
    return filters


def merchant_filter(
    merchant_id: Optional[Union[str, UUID]] = None,
    merchant_domain: Optional[str] = None
) -> Dict[str, Any]:
    """
    Alias for shop_filter using merchant terminology.
    
    Args:
        merchant_id: Merchant UUID
        merchant_domain: Merchant domain
        
    Returns:
        Filter dictionary with merchantId/merchantDomain fields
        
    Example:
        products = await db.product.find_many(
            where=merchant_filter(merchant_id=merchant_id)
        )
    """
    filters = {}
    
    if merchant_id:
        filters["merchantId"] = str(merchant_id)
    
    if merchant_domain:
        filters["merchantDomain"] = merchant_domain
    
    if merchant_id and merchant_domain:
        return {"AND": [
            {"merchantId": str(merchant_id)},
            {"merchantDomain": merchant_domain}
        ]}
    
    return filters


def soft_delete_filter(
    include_deleted: bool = False,
    table_alias: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate filter for soft-deleted records.
    
    Args:
        include_deleted: Whether to include soft-deleted records
        table_alias: Optional table alias for nested queries
        
    Returns:
        Filter dictionary for Prisma where clause
        
    Example:
        # Exclude soft-deleted records (default)
        products = await db.product.find_many(
            where=soft_delete_filter()
        )
        
        # Include soft-deleted records
        all_products = await db.product.find_many(
            where=soft_delete_filter(include_deleted=True)
        )
    """
    if include_deleted:
        return {}
    
    base_filter = {"isDeleted": False}
    
    if table_alias:
        return {table_alias: base_filter}
    
    return base_filter


def pagination_args(
    page: int = 1,
    limit: int = 50,
    max_limit: int = 1000
) -> Dict[str, int]:
    """
    Generate pagination arguments for Prisma queries.
    
    Args:
        page: Page number (1-based)
        limit: Items per page
        max_limit: Maximum allowed items per page
        
    Returns:
        Dictionary with 'skip' and 'take' for Prisma
        
    Example:
        products = await db.product.find_many(
            **pagination_args(page=2, limit=20)
        )
    """
    # Ensure valid page
    page = max(1, page)
    
    # Ensure limit is within bounds
    limit = min(max(1, limit), max_limit)
    
    return {
        "skip": (page - 1) * limit,
        "take": limit
    }


class OrderDirection(str, Enum):
    """Order direction for sorting."""
    ASC = "asc"
    DESC = "desc"


def parse_order_by(
    order_by: Optional[str] = None,
    allowed_fields: Optional[List[str]] = None,
    default_field: str = "createdAt",
    default_direction: OrderDirection = OrderDirection.DESC
) -> List[Dict[str, str]]:
    """
    Parse order_by string into Prisma orderBy format.
    
    Args:
        order_by: Comma-separated fields with optional direction (e.g., "name,-createdAt")
        allowed_fields: List of allowed field names (None allows all)
        default_field: Default field to sort by
        default_direction: Default sort direction
        
    Returns:
        List of orderBy dictionaries for Prisma
        
    Example:
        # Sort by name ascending, then createdAt descending
        products = await db.product.find_many(
            order_by=parse_order_by("name,-createdAt")
        )
        
        # With field restrictions
        products = await db.product.find_many(
            order_by=parse_order_by(
                "name,-price",
                allowed_fields=["name", "price", "createdAt"]
            )
        )
    """
    if not order_by:
        return [{default_field: default_direction.value}]
    
    order_list = []
    
    for field_spec in order_by.split(","):
        field_spec = field_spec.strip()
        if not field_spec:
            continue
            
        # Check for descending prefix
        if field_spec.startswith("-"):
            field = field_spec[1:]
            direction = OrderDirection.DESC
        else:
            field = field_spec
            direction = OrderDirection.ASC
        
        # Validate field if restrictions are set
        if allowed_fields and field not in allowed_fields:
            continue
            
        order_list.append({field: direction.value})
    
    # Use default if no valid fields
    if not order_list:
        return [{default_field: default_direction.value}]
    
    return order_list


# Optional: Add more helpers as needed
def build_search_filter(
    search_term: Optional[str],
    search_fields: List[str],
    mode: str = "insensitive"
) -> Dict[str, Any]:
    """
    Build a search filter for multiple fields.
    
    Args:
        search_term: The search term
        search_fields: List of fields to search in
        mode: Prisma search mode ('insensitive' or 'default')
        
    Returns:
        OR filter for Prisma where clause
        
    Example:
        # Search in multiple fields
        products = await db.product.find_many(
            where=build_search_filter(
                "shirt",
                ["name", "description", "sku"]
            )
        )
    """
    if not search_term or not search_fields:
        return {}
    
    return {
        "OR": [
            {field: {"contains": search_term, "mode": mode}}
            for field in search_fields
        ]
    }


def combine_filters(*filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine multiple filter dictionaries with AND logic.
    
    Args:
        *filters: Variable number of filter dictionaries
        
    Returns:
        Combined filter dictionary
        
    Example:
        products = await db.product.find_many(
            where=combine_filters(
                {"merchantId": merchant_id},
                soft_delete_filter(),
                build_search_filter(search, ["name", "sku"])
            )
        )
    """
    # Remove empty filters
    valid_filters = [f for f in filters if f]
    
    if not valid_filters:
        return {}
    
    if len(valid_filters) == 1:
        return valid_filters[0]
    
    return {"AND": valid_filters}


# ============ USAGE EXAMPLES ============
"""
Common usage patterns for filtering:

1. Filter products by shop:
```python
# Using shop_filter
products = await db.product.find_many(
    where=combine_filters(
        shop_filter(shop_id=shop_id),
        soft_delete_filter()
    )
)

# Using merchant_filter (same result, different field names)
products = await db.product.find_many(
    where=combine_filters(
        merchant_filter(merchant_id=merchant_id),
        soft_delete_filter()
    )
)
```

2. Filter with pagination and search:
```python
products = await db.product.find_many(
    where=combine_filters(
        merchant_filter(merchant_id=merchant_id, merchant_domain=domain),
        soft_delete_filter(),
        build_search_filter(search_term, ["name", "description", "sku"])
    ),
    order_by=parse_order_by("-updatedAt,name"),
    **pagination_args(page=2, limit=20)
)
```

3. Filter nested relations:
```python
# If your schema has orders with a merchant relation
orders = await db.order.find_many(
    where={
        "merchant": merchant_filter(merchant_id=merchant_id)
    },
    include={"merchant": True}
)
```
"""