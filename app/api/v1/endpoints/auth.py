"""
Authentication endpoints: register, login, refresh, me.
"""
from fastapi import APIRouter
from app.api.deps import DbSession, CurrentUser
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
)
from app.schemas.base import MessageResponse

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
