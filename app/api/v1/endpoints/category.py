"""
Category CRUD endpoints.
"""
import uuid
import math
from typing import Optional
from fastapi import APIRouter, Query
from app.api.deps import DbSession, CurrentUser, ManagerUser
from app.services.category_service import CategoryService
from app.schemas.product import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.base import PaginationParams, PaginatedResponse, MessageResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
    summary="Create a new category",
)
async def create_category(
    data: CategoryCreate,
    db: DbSession,
    _: ManagerUser,
):
    return await CategoryService(db).create(data)


@router.get(
    "",
    response_model=PaginatedResponse[CategoryResponse],
    summary="List all categories (paginated)",
)
async def list_categories(
    db: DbSession,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
):
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = await CategoryService(db).list_all(pagination, active_only)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category by ID",
)
async def get_category(
    category_id: uuid.UUID,
    db: DbSession,
    _: CurrentUser,
):
    return await CategoryService(db).get_by_id(category_id)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category",
)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: DbSession,
    _: ManagerUser,
):
    return await CategoryService(db).update(category_id, data)


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    summary="Soft-delete a category",
)
async def delete_category(
    category_id: uuid.UUID,
    db: DbSession,
    _: ManagerUser,
):
    await CategoryService(db).delete(category_id)
    return MessageResponse(message="Category deactivated successfully")
