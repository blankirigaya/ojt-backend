"""
Sale model - records individual sales transactions.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, Integer, ForeignKey,
    DateTime, Date, func, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.db.session import Base
from app.models.mixins import TimestampMixin


class SaleSource(str, enum.Enum):
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    API = "api"


class Sale(Base, TimestampMixin):
    __tablename__ = "sales"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Sale details
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Source tracking
    source: Mapped[SaleSource] = mapped_column(
        SAEnum(SaleSource), default=SaleSource.MANUAL, nullable=False
    )
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship(  # noqa: F821
        "Product", back_populates="sales"
    )

    def __repr__(self) -> str:
        return f"<Sale id={self.id} product_id={self.product_id} qty={self.quantity} date={self.sale_date}>"
