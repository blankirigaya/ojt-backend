"""
Supplier CRUD endpoints.
"""
import uuid
import math
from fastapi import APIRouter, Query
from app.api.deps import DbSession, CurrentUser, ManagerUser
from app.services.supplier_service import SupplierService
from app.schemas.product import SupplierCreate, SupplierUpdate, SupplierResponse
from app.schemas.base import PaginationParams, PaginatedResponse, MessageResponse

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=201,
    summary="Create a new supplier",
)
async def create_supplier(
    data: SupplierCreate,
    db: DbSession,
    _: ManagerUser,
):
    return await SupplierService(db).create(data)


@router.get(
    "",
    response_model=PaginatedResponse[SupplierResponse],
    summary="List all suppliers (paginated)",
)
async def list_suppliers(
    db: DbSession,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
):
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = await SupplierService(db).list_all(pagination, active_only)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get a supplier by ID",
)
async def get_supplier(
    supplier_id: uuid.UUID,
    db: DbSession,
    _: CurrentUser,
):
    return await SupplierService(db).get_by_id(supplier_id)


@router.patch(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update a supplier",
)
async def update_supplier(
    supplier_id: uuid.UUID,
    data: SupplierUpdate,
    db: DbSession,
    _: ManagerUser,
):
    return await SupplierService(db).update(supplier_id, data)


@router.delete(
    "/{supplier_id}",
    response_model=MessageResponse,
    summary="Soft-delete a supplier",
)
async def delete_supplier(
    supplier_id: uuid.UUID,
    db: DbSession,
    _: ManagerUser,
):
    await SupplierService(db).delete(supplier_id)
    return MessageResponse(message="Supplier deactivated successfully")
