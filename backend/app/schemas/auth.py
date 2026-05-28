"""Auth request and response DTOs."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login payload."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=3, max_length=128)


class RegisterRequest(BaseModel):
    """Registration payload."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Access and refresh JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token payload used for refresh and logout."""

    refresh_token: str
