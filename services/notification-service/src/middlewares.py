from fastapi import FastAPI
from shared.api.middleware import setup_api_middleware
from .config import ServiceConfig

def add_middleware(app: FastAPI, config: ServiceConfig):
    """Add all middleware to app using shared components"""
    
    # Use shared API middleware for standardized responses and error handling
    setup_api_middleware(
        app,
        service_name=config.SERVICE_NAME,
        include_error_details=config.DEBUG
    )
    
    # Additional service-specific middleware can be added here if needed