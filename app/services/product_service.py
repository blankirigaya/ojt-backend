"""
Product service.
Handles full CRUD, stock management, and low-stock queries.
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductSummary,
)
from app.schemas.base import PaginationParams
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Helpers ───────────────────────────────────────────────────────────────
    async def _get_or_404(self, product_id: uuid.UUID) -> Product:
        product = await self.db.scalar(
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.supplier),
            )
            .where(Product.id == product_id)
        )
        if not product:
            raise NotFoundException("Product", product_id)
        return product

    # ── CRUD ──────────────────────────────────────────────────────────────────
    async def create(self, data: ProductCreate) -> ProductResponse:
        """Create a new product. SKU must be unique."""
        existing = await self.db.scalar(
            select(Product).where(Product.sku == data.sku)
        )
        if existing:
            raise ConflictException(f"Product with SKU '{data.sku}' already exists")

        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.flush()

        # Reload with relationships
        product = await self._get_or_404(product.id)
        return ProductResponse.model_validate(product)

    async def get_by_id(self, product_id: uuid.UUID) -> ProductResponse:
        product = await self._get_or_404(product_id)
        return ProductResponse.model_validate(product)

    async def list_products(
        self,
        pagination: PaginationParams,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        supplier_id: Optional[uuid.UUID] = None,
        low_stock_only: bool = False,
        active_only: bool = True,
    ) -> Tuple[List[ProductResponse], int]:
        """Paginated product list with optional filters."""
        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.supplier),
            )
        )

        if active_only:
            query = query.where(Product.is_active == True)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Product.name.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            )
        if category_id:
            query = query.where(Product.category_id == category_id)
        if supplier_id:
            query = query.where(Product.supplier_id == supplier_id)
        if low_stock_only:
            # current_stock <= reorder_point
            query = query.where(Product.current_stock <= Product.reorder_point)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        result = await self.db.scalars(
            query.order_by(Product.name)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        items = [ProductResponse.model_validate(p) for p in result.all()]
        return items, total

    async def update(
        self, product_id: uuid.UUID, data: ProductUpdate
    ) -> ProductResponse:
        product = await self._get_or_404(product_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        await self.db.flush()
        await self.db.refresh(product)
        product = await self._get_or_404(product_id)
        return ProductResponse.model_validate(product)

    async def delete(self, product_id: uuid.UUID) -> None:
        """Soft-delete a product."""
        product = await self._get_or_404(product_id)
        product.is_active = False
        await self.db.flush()

    # ── Stock management ──────────────────────────────────────────────────────
    async def deduct_stock(self, product_id: uuid.UUID, quantity: int) -> Product:
        """
        Deduct stock after a sale. Raises BadRequestException on insufficient stock.
        Returns the updated Product ORM object (for use within a transaction).
        """
        product = await self.db.get(Product, product_id)
        if not product:
            raise NotFoundException("Product", product_id)
        if product.current_stock < quantity:
            raise BadRequestException(
                f"Insufficient stock for '{product.name}': "
                f"available={product.current_stock}, requested={quantity}"
            )
        product.current_stock -= quantity
        await self.db.flush()
        return product

    async def adjust_stock(
        self, product_id: uuid.UUID, adjustment: int, reason: str = ""
    ) -> ProductResponse:
        """
        Manually adjust stock (positive = add, negative = remove).
        """
        product = await self.db.get(Product, product_id)
        if not product:
            raise NotFoundException("Product", product_id)

        new_stock = product.current_stock + adjustment
        if new_stock < 0:
            raise BadRequestException(
                f"Stock adjustment would result in negative stock "
                f"(current={product.current_stock}, adjustment={adjustment})"
            )
        product.current_stock = new_stock
        await self.db.flush()
        await self.db.refresh(product)
        return ProductResponse.model_validate(product)

    async def get_low_stock_products(self) -> List[ProductSummary]:
        """Return all active products at or below their reorder point."""
        result = await self.db.scalars(
            select(Product)
            .where(
                Product.is_active == True,
                Product.current_stock <= Product.reorder_point,
            )
            .order_by(Product.current_stock)
        )
        return [ProductSummary.model_validate(p) for p in result.all()]

    async def get_dashboard_stats(self) -> dict:
        """Aggregate stats for the dashboard KPI cards."""
        total_products = await self.db.scalar(
            select(func.count(Product.id)).where(Product.is_active == True)
        ) or 0

        low_stock_count = await self.db.scalar(
            select(func.count(Product.id)).where(
                Product.is_active == True,
                Product.current_stock <= Product.reorder_point,
            )
        ) or 0

        out_of_stock = await self.db.scalar(
            select(func.count(Product.id)).where(
                Product.is_active == True,
                Product.current_stock == 0,
            )
        ) or 0

        # Total inventory value = SUM(cost_price * current_stock)
        from sqlalchemy import cast, Float
        total_value = await self.db.scalar(
            select(func.sum(Product.cost_price * Product.current_stock)).where(
                Product.is_active == True
            )
        ) or 0.0

        return {
            "total_products": total_products,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock,
            "total_inventory_value": float(total_value),
        }
