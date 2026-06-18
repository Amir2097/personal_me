"""Auth request and response DTOs."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login payload."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=3, max_length=128)


class RegisterRequest(BaseModel):
    """Registration payload."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr | None = None


class TokenResponse(BaseModel):
    """Access and refresh JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    username: str = ""
    is_admin: bool = False


class UserProfile(BaseModel):
    """Профиль текущего пользователя."""

    username: str
    is_admin: bool


class RefreshTokenRequest(BaseModel):
    """Refresh token payload used for refresh and logout."""

    refresh_token: str | None = None


class AuthConfigResponse(BaseModel):
    """Публичные настройки auth для фронтенда."""

    allow_registration: bool
    expose_reset_token: bool
    password_reset_via_email: bool


class SsoExchangeRequest(BaseModel):
    """Обмен одноразового SSO-кода."""

    code: str = Field(..., min_length=8, max_length=128)


class SsoExchangeResponse(BaseModel):
    """Результат обмена SSO-кода."""

    username: str
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Запрос токена сброса пароля."""

    username: str = Field(..., min_length=3, max_length=64)


class PasswordResetConfirm(BaseModel):
    """Подтверждение сброса пароля по токену."""

    token: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Смена пароля авторизованным пользователем."""

    current_password: str = Field(..., min_length=3, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetTokenResponse(BaseModel):
    """Ответ с токеном сброса (для dev/terminal flow без email)."""

    message: str
    reset_token: str | None = None
    expires_in_minutes: int
