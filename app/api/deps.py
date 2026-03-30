"""
FastAPI dependency injection helpers.
Provides get_current_user, require_admin, etc.
"""
from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService
from app.core.exceptions import ForbiddenException, UnauthorizedException

# Bearer token extractor — auto_error=False so we can give a better message
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and validate the JWT Bearer token. Returns the User ORM object."""
    if not credentials:
        raise UnauthorizedException("No authentication token provided")

    service = AuthService(db)
    return await service.get_current_user(credentials.credentials)


async def require_manager(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require at least manager role."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise ForbiddenException("Manager or Admin role required")
    return current_user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Admin role required")
    return current_user


# Typed aliases for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
ManagerUser = Annotated[User, Depends(require_manager)]
AdminUser = Annotated[User, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
