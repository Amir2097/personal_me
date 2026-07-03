"""Auth request and response DTOs."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.email_validation import normalize_optional_email


class LoginRequest(BaseModel):
    """Login payload."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=3, max_length=128)


class RegisterRequest(BaseModel):
    """Registration payload."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr | None = None
    accept_terms: bool = Field(
        ...,
        description="Согласие с политикой конфиденциальности и пользовательским соглашением",
    )


class TokenResponse(BaseModel):
    """Access and refresh JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    username: str = ""
    is_admin: bool = False
    role: str = "user"


class UserProfile(BaseModel):
    """Профиль текущего пользователя."""

    username: str
    is_admin: bool
    role: str = "user"
    email: str | None = None
    display_name: str = ""
    avatar_url: str = ""
    bio: str = ""
    location: str = ""
    website: str = ""
    telegram: str = ""
    github: str = ""
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class UserProfileUpdate(BaseModel):
    """Обновление профиля пользователя."""

    email: str | None = None
    display_name: str | None = Field(default=None, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=512)
    bio: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=128)
    website: str | None = Field(default=None, max_length=256)
    telegram: str | None = Field(default=None, max_length=128)
    github: str | None = Field(default=None, max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_optional_email(value)

    @field_validator("display_name", "avatar_url", "bio", "location", "website", "telegram", "github")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


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
    new_password_confirm: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.new_password_confirm:
            raise ValueError("Новый пароль и подтверждение не совпадают.")
        return self


class PasswordResetTokenResponse(BaseModel):
    """Ответ с токеном сброса (для dev/terminal flow без email)."""

    message: str
    reset_token: str | None = None
    expires_in_minutes: int
