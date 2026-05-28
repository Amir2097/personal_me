"""Authentication endpoints."""

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.core.db import get_session
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import (
    login_user,
    logout_user,
    refresh_user_tokens,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and issue JWT token",
    description=(
        "Authenticates user against database credentials and returns "
        "access/refresh bearer JWT tokens."
    ),
)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    """Issue JWT token pair for valid credentials."""
    return login_user(session, payload.username, payload.password)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register user and issue JWT tokens",
    description=(
        "Creates a new user with hashed password in database and returns "
        "access/refresh bearer JWT tokens."
    ),
)
def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> TokenResponse:
    """Register a new user and issue token pair."""
    return register_user(session, payload.username, payload.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh JWT token pair",
    description=(
        "Validates refresh token, revokes previous refresh token, and "
        "returns new access/refresh token pair."
    ),
)
def refresh(
    payload: RefreshTokenRequest, session: Session = Depends(get_session)
) -> TokenResponse:
    """Refresh token pair using refresh token."""
    return refresh_user_tokens(session, payload.refresh_token)


@router.post(
    "/logout",
    status_code=204,
    summary="Logout and revoke refresh token",
    description="Revokes provided refresh token so it cannot be reused.",
)
def logout(payload: RefreshTokenRequest, session: Session = Depends(get_session)) -> Response:
    """Logout user by revoking refresh token."""
    logout_user(session, payload.refresh_token)
    return Response(status_code=204)
