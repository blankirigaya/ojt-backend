"""
Product model - core inventory entity.
"""
import uuid
from decimal import Decimal
from sqlalchemy import (
    String, Text, Boolean, Numeric, Integer, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base
from app.models.mixins import TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Pricing
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # Stock
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    reorder_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    max_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=500)

    # Relations
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    category: Mapped["Category"] = relationship(  # noqa: F821
        "Category", back_populates="products"
    )
    supplier: Mapped["Supplier"] = relationship(  # noqa: F821
        "Supplier", back_populates="products"
    )
    sales: Mapped[list["Sale"]] = relationship(  # noqa: F821
        "Sale", back_populates="product", lazy="select"
    )
    forecasts: Mapped[list["Forecast"]] = relationship(  # noqa: F821
        "Forecast", back_populates="product", lazy="select"
    )

    # Composite index for common filter queries
    __table_args__ = (
        Index("ix_products_category_active", "category_id", "is_active"),
    )

    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.reorder_point

    @property
    def stock_value(self) -> Decimal:
        return self.cost_price * self.current_stock

    def __repr__(self) -> str:
        return f"<Product sku={self.sku} name={self.name} stock={self.current_stock}>"
