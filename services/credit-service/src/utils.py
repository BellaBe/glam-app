def normalize_shop_domain(domain: str) -> str:
    """Normalize shop domain to lowercase .myshopify.com format"""
    if not domain:
        return domain
    
    domain = domain.lower().strip()
    
    # Ensure it ends with .myshopify.com
    if not domain.endswith('.myshopify.com'):
        # If it's just the shop name, append the domain
        if '.' not in domain:
            domain = f"{domain}.myshopify.com"
        else:
            raise ValueError(f"Invalid shop domain format: {domain}")
    
    return domain

