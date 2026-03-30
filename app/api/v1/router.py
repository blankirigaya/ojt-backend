"""
API v1 router — assembles all endpoint sub-routers.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, category, supplier, products

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(category.router)
api_router.include_router(supplier.router)
api_router.include_router(products.router)
