"""
Sale and Forecast Pydantic schemas.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import field_validator

from app.schemas.base import BaseSchema
from app.models.sale import SaleSource
from app.models.forecast import ForecastStatus


# ── Sale ──────────────────────────────────────────────────────────────────────
class SaleCreate(BaseSchema):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    sale_date: date
    source: SaleSource = SaleSource.MANUAL
    reference_number: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

    @field_validator("unit_price")
    @classmethod
    def price_positive(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Unit price cannot be negative")
        return v


class SaleUpdate(BaseSchema):
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    sale_date: Optional[date] = None
    notes: Optional[str] = None


class SaleResponse(BaseSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    sale_date: date
    source: SaleSource
    reference_number: Optional[str]
    notes: Optional[str]


class SaleWithProduct(SaleResponse):
    """Sale response enriched with product info."""
    product_name: Optional[str] = None
    product_sku: Optional[str] = None


# ── Forecast ──────────────────────────────────────────────────────────────────
class ForecastRequest(BaseSchema):
    product_id: uuid.UUID
    horizon_days: int = 90
    model_name: str = "prophet"

    @field_validator("horizon_days")
    @classmethod
    def horizon_valid(cls, v: int) -> int:
        if not 7 <= v <= 365:
            raise ValueError("Forecast horizon must be between 7 and 365 days")
        return v


class ForecastDataPoint(BaseSchema):
    ds: date
    yhat: float
    yhat_lower: float
    yhat_upper: float


class ForecastResponse(BaseSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    model_name: str
    status: ForecastStatus
    forecast_from: date
    forecast_to: date
    horizon_days: int
    mae: Optional[float]
    rmse: Optional[float]
    mape: Optional[float]
    predictions: Optional[List[Any]]
    error_message: Optional[str]


class ForecastMetrics(BaseSchema):
    mae: float
    rmse: float
    mape: float
    model_name: str
    horizon_days: int
