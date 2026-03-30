"""
Category CRUD service.
"""
import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.categories import Category
from app.schemas.product import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.base import PaginationParams
from app.core.exceptions import NotFoundException, ConflictException


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CategoryCreate) -> CategoryResponse:
        existing = await self.db.scalar(
            select(Category).where(Category.name == data.name)
        )
        if existing:
            raise ConflictException(f"Category '{data.name}' already exists")

        category = Category(**data.model_dump())
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return CategoryResponse.model_validate(category)

    async def get_by_id(self, category_id: uuid.UUID) -> CategoryResponse:
        category = await self.db.get(Category, category_id)
        if not category:
            raise NotFoundException("Category", category_id)
        return CategoryResponse.model_validate(category)

    async def list_all(
        self,
        pagination: PaginationParams,
        active_only: bool = True,
    ) -> Tuple[List[CategoryResponse], int]:
        query = select(Category)
        if active_only:
            query = query.where(Category.is_active == True)

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.scalars(
            query.offset(pagination.offset).limit(pagination.page_size)
        )
        items = [CategoryResponse.model_validate(c) for c in result.all()]
        return items, total or 0

    async def update(
        self, category_id: uuid.UUID, data: CategoryUpdate
    ) -> CategoryResponse:
        category = await self.db.get(Category, category_id)
        if not category:
            raise NotFoundException("Category", category_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)

        await self.db.flush()
        await self.db.refresh(category)
        return CategoryResponse.model_validate(category)

    async def delete(self, category_id: uuid.UUID) -> None:
        category = await self.db.get(Category, category_id)
        if not category:
            raise NotFoundException("Category", category_id)
        # Soft delete
        category.is_active = False
        await self.db.flush()
