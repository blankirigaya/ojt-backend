"""
Centralized exception definitions.
All domain-specific errors inherit from AppException for consistent handling.
"""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception with HTTP status code and detail."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)


class NotFoundException(AppException):
    def __init__(self, resource: str, identifier: Any = None):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with id '{identifier}' not found"
        super().__init__(status_code=404, detail=detail)


class ConflictException(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=403, detail=detail)


class ValidationException(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)


class BadRequestException(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)
