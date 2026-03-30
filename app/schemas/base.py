"""
Shared Pydantic base schemas and pagination utilities.
"""
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


class BaseSchema(BaseModel):
    """All schemas inherit from this for consistent config."""
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Query params for paginated endpoints."""
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema, Generic[DataT]):
    """Generic paginated response wrapper."""
    items: List[DataT]
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


class ErrorResponse(BaseModel):
    """Structured error response."""
    detail: str
    code: Optional[str] = None
