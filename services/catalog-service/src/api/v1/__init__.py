# src/api/router.py
from fastapi import APIRouter
from .v1 import sync, products

router = APIRouter()
router.include_router(sync.router)
router.include_router(products.router)