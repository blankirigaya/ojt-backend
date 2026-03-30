"""
Supplier CRUD service.
"""
import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.suppliers import Supplier
from app.schemas.product import SupplierCreate, SupplierUpdate, SupplierResponse
from app.schemas.base import PaginationParams
from app.core.exceptions import NotFoundException, ConflictException


class SupplierService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SupplierCreate) -> SupplierResponse:
        existing = await self.db.scalar(
            select(Supplier).where(Supplier.name == data.name)
        )
        if existing:
            raise ConflictException(f"Supplier '{data.name}' already exists")

        supplier = Supplier(**data.model_dump())
        self.db.add(supplier)
        await self.db.flush()
        await self.db.refresh(supplier)
        return SupplierResponse.model_validate(supplier)

    async def get_by_id(self, supplier_id: uuid.UUID) -> SupplierResponse:
        supplier = await self.db.get(Supplier, supplier_id)
        if not supplier:
            raise NotFoundException("Supplier", supplier_id)
        return SupplierResponse.model_validate(supplier)

    async def list_all(
        self,
        pagination: PaginationParams,
        active_only: bool = True,
    ) -> Tuple[List[SupplierResponse], int]:
        query = select(Supplier)
        if active_only:
            query = query.where(Supplier.is_active == True)

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.scalars(
            query.offset(pagination.offset).limit(pagination.page_size)
        )
        items = [SupplierResponse.model_validate(s) for s in result.all()]
        return items, total or 0

    async def update(
        self, supplier_id: uuid.UUID, data: SupplierUpdate
    ) -> SupplierResponse:
        supplier = await self.db.get(Supplier, supplier_id)
        if not supplier:
            raise NotFoundException("Supplier", supplier_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(supplier, field, value)

        await self.db.flush()
        await self.db.refresh(supplier)
        return SupplierResponse.model_validate(supplier)

    async def delete(self, supplier_id: uuid.UUID) -> None:
        supplier = await self.db.get(Supplier, supplier_id)
        if not supplier:
            raise NotFoundException("Supplier", supplier_id)
        supplier.is_active = False
        await self.db.flush()
