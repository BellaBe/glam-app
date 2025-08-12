# src/api/v1/__init__.py
from fastapi import APIRouter
from .merchants import merchants_router

v1_router = APIRouter(prefix="/v1")

# Include merchant routes
v1_router.include_router(merchants_router, tags=["merchants"])