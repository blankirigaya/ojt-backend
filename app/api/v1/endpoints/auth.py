"""
Authentication endpoints: register, login, refresh, me, admin create-user.
"""
from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional

from app.api.deps import DbSession, CurrentUser
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
)
from app.schemas.base import MessageResponse
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user account",
)
async def register(data: RegisterRequest, db: DbSession):
    return await AuthService(db).register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
)
async def login(data: LoginRequest, db: DbSession):
    return await AuthService(db).login(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Obtain a new access token using a refresh token",
)
async def refresh_token(refresh_token: str, db: DbSession):
    return await AuthService(db).refresh_token(refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
async def me(current_user: CurrentUser):
    return UserResponse.model_validate(current_user)


@router.post(
    "/admin/create-user",
    response_model=UserResponse,
    status_code=201,
    summary="[Admin] Create a new user — protected by X-Admin-Secret header",
    description=(
        "Creates a new user account. Requires the `X-Admin-Secret` header to match "
        "the `ADMIN_SECRET` environment variable set on the server. "
        "Use this when you don't have shell access (e.g. Render free tier)."
    ),
)
async def admin_create_user(
    data: RegisterRequest,
    db: DbSession,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """
    Protected admin endpoint to create users without shell access.
    Set ADMIN_SECRET in Render's Environment Variables dashboard, then
    pass it as the X-Admin-Secret header when calling this endpoint.
    """
    if not settings.ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin user creation is not configured. Set the ADMIN_SECRET environment variable.",
        )

    if x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin secret.",
        )

    return await AuthService(db).register(data)
