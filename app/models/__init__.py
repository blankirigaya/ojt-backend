"""
Import all models here so Alembic can discover them via Base.metadata.
"""
from app.models.user import User, UserRole
from app.models.categories import Category
from app.models.suppliers import Supplier
from app.models.product import Product
from app.models.sale import Sale, SaleSource
from app.models.forecast import Forecast, ForecastStatus

__all__ = [
    "User", "UserRole",
    "Category",
    "Supplier",
    "Product",
    "Sale", "SaleSource",
    "Forecast", "ForecastStatus",
]
