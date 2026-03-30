"""
Product, Category, and Supplier Pydantic schemas.
"""
import uuid
from decimal import Decimal
from typing import Optional
from pydantic import field_validator
from app.schemas.base import BaseSchema


# ── Category ──────────────────────────────────────────────────────────────────
class CategoryCreate(BaseSchema):
    name: str
    description: Optional[str] = None


class CategoryUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseSchema):
    id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool


# ── Supplier ──────────────────────────────────────────────────────────────────
class SupplierCreate(BaseSchema):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class SupplierUpdate(BaseSchema):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseSchema):
    id: uuid.UUID
    name: str
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    is_active: bool


# ── Product ───────────────────────────────────────────────────────────────────
class ProductCreate(BaseSchema):
    sku: str
    name: str
    description: Optional[str] = None
    cost_price: Decimal
    selling_price: Decimal
    current_stock: int = 0
    reorder_point: int = 10
    reorder_quantity: int = 50
    max_stock: int = 500
    category_id: Optional[uuid.UUID] = None
    supplier_id: Optional[uuid.UUID] = None

    @field_validator("selling_price", "cost_price")
    @classmethod
    def price_positive(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v

    @field_validator("current_stock", "reorder_point", "reorder_quantity", "max_stock")
    @classmethod
    def qty_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v


class ProductUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    current_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    max_stock: Optional[int] = None
    category_id: Optional[uuid.UUID] = None
    supplier_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseSchema):
    id: uuid.UUID
    sku: str
    name: str
    description: Optional[str]
    cost_price: Decimal
    selling_price: Decimal
    current_stock: int
    reorder_point: int
    reorder_quantity: int
    max_stock: int
    is_active: bool
    is_low_stock: bool
    category_id: Optional[uuid.UUID]
    supplier_id: Optional[uuid.UUID]
    category: Optional[CategoryResponse] = None
    supplier: Optional[SupplierResponse] = None


class ProductSummary(BaseSchema):
    """Lightweight product for dropdowns and lists."""
    id: uuid.UUID
    sku: str
    name: str
    current_stock: int
    is_low_stock: bool
