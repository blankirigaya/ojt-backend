"""
Authentication service.
Handles user registration, login, and token operations.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.exceptions import (
    ConflictException, UnauthorizedException, NotFoundException,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> UserResponse:
        """Register a new user. Raises ConflictException if email exists."""
        existing = await self.db.scalar(
            select(User).where(User.email == data.email)
        )
        if existing:
            raise ConflictException(f"Email '{data.email}' is already registered")

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()  # Get the generated ID before commit
        await self.db.refresh(user)
        return UserResponse.model_validate(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT tokens."""
        user = await self.db.scalar(
            select(User).where(User.email == data.email)
        )
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Issue new access token from a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise UnauthorizedException("Invalid token type")
            user_id = payload["sub"]
        except Exception:
            raise UnauthorizedException("Invalid or expired refresh token")

        user = await self.db.get(User, uuid.UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def get_current_user(self, token: str) -> User:
        """Decode access token and return the authenticated User ORM object."""
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise UnauthorizedException("Invalid token type")
            user_id = payload["sub"]
        except Exception:
            raise UnauthorizedException("Invalid or expired token")

        user = await self.db.get(User, uuid.UUID(user_id))
        if not user:
            raise NotFoundException("User")
        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")
        return user
