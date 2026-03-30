"""
Product CRUD endpoints.
Includes search/filter, stock adjustment, and low-stock alerts.
"""
import uuid
import math
from typing import Optional
from fastapi import APIRouter, Query
from app.api.deps import DbSession, CurrentUser, ManagerUser
from app.services.product_service import ProductService
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductSummary,
)
from app.schemas.base import PaginationParams, PaginatedResponse, MessageResponse
from pydantic import BaseModel

router = APIRouter(prefix="/products", tags=["Products"])


class StockAdjustRequest(BaseModel):
    adjustment: int
    reason: str = ""


@router.post(
    "",
    response_model=ProductResponse,
    status_code=201,
    summary="Create a new product",
)
async def create_product(
    data: ProductCreate,
    db: DbSession,
    _: ManagerUser,
):
    return await ProductService(db).create(data)


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    summary="List products with optional search and filters",
)
async def list_products(
    db: DbSession,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    category_id: Optional[uuid.UUID] = Query(None),
    supplier_id: Optional[uuid.UUID] = Query(None),
    low_stock_only: bool = Query(False),
    active_only: bool = Query(True),
):
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = await ProductService(db).list_products(
        pagination=pagination,
        search=search,
        category_id=category_id,
        supplier_id=supplier_id,
        low_stock_only=low_stock_only,
        active_only=active_only,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get(
    "/alerts/low-stock",
    response_model=list[ProductSummary],
    summary="Get all products at or below reorder point",
)
async def low_stock_alerts(
    db: DbSession,
    _: CurrentUser,
):
    return await ProductService(db).get_low_stock_products()


@router.get(
    "/stats/dashboard",
    response_model=dict,
    summary="Get inventory KPI stats for dashboard",
)
async def dashboard_stats(
    db: DbSession,
    _: CurrentUser,
):
    return await ProductService(db).get_dashboard_stats()


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID",
)
async def get_product(
    product_id: uuid.UUID,
    db: DbSession,
    _: CurrentUser,
):
    return await ProductService(db).get_by_id(product_id)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: DbSession,
    _: ManagerUser,
):
    return await ProductService(db).update(product_id, data)


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Soft-delete a product",
)
async def delete_product(
    product_id: uuid.UUID,
    db: DbSession,
    _: ManagerUser,
):
    await ProductService(db).delete(product_id)
    return MessageResponse(message="Product deactivated successfully")


@router.post(
    "/{product_id}/adjust-stock",
    response_model=ProductResponse,
    summary="Manually adjust stock level (positive=add, negative=remove)",
)
async def adjust_stock(
    product_id: uuid.UUID,
    body: StockAdjustRequest,
    db: DbSession,
    _: ManagerUser,
):
    return await ProductService(db).adjust_stock(
        product_id, body.adjustment, body.reason
    )
