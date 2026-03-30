"""
Forecast model - stores ML forecast results per product.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Integer, ForeignKey,
    DateTime, Date, func, JSON, Float, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.db.session import Base
from app.models.mixins import TimestampMixin


class ForecastStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Forecast(Base, TimestampMixin):
    __tablename__ = "forecasts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Forecast metadata
    model_name: Mapped[str] = mapped_column(String(50), default="prophet", nullable=False)
    status: Mapped[ForecastStatus] = mapped_column(
        SAEnum(ForecastStatus), default=ForecastStatus.PENDING, nullable=False
    )

    # Forecast window
    forecast_from: Mapped[date] = mapped_column(Date, nullable=False)
    forecast_to: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Performance metrics (None until training completes)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Forecast data stored as JSON array: [{ds, yhat, yhat_lower, yhat_upper}, ...]
    predictions: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship(  # noqa: F821
        "Product", back_populates="forecasts"
    )

    def __repr__(self) -> str:
        return (
            f"<Forecast id={self.id} product_id={self.product_id} "
            f"status={self.status} model={self.model_name}>"
        )
