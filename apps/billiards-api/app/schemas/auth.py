"""Auth request and response DTOs."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.email_validation import normalize_optional_email, normalize_required_email


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=3, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(..., min_length=5, max_length=256)
    accept_terms: bool = Field(
        ...,
        description="Согласие с политикой конфиденциальности и пользовательским соглашением",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_required_email(value)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    username: str = ""
    role: str = "player"
    email_verified: bool = False


class LoginResponse(BaseModel):
    requires_totp: bool = False
    challenge_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    username: str = ""
    role: str = "player"
    email_verified: bool = False


class RegisterResponse(BaseModel):
    message: str
    username: str
    verification_required: bool = False
    verification_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None


class MeResponse(BaseModel):
    username: str
    source: str
    role: str | None = None
    email: str | None = None
    email_verified: bool | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    is_admin: bool = False


class UserProfile(BaseModel):
    username: str
    email: str
    role: str
    display_name: str = ""
    avatar_url: str = ""
    bio: str = ""
    location: str = ""
    telegram: str = ""
    email_verified: bool
    is_active: bool
    totp_enabled: bool = False
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class UserProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=64)
    bio: str | None = Field(default=None, max_length=280)
    location: str | None = Field(default=None, max_length=128)
    telegram: str | None = Field(default=None, max_length=64)

    @field_validator("display_name", "bio", "location", "telegram")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class AuthConfigResponse(BaseModel):
    allow_registration: bool
    require_email_verification: bool
    expose_reset_token: bool
    expose_verification_token: bool
    password_reset_via_email: bool
    email_verification_via_email: bool
    allow_legacy_admin_key: bool


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=8, max_length=128)


class ResendVerificationRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=128)


class ResendVerificationResponse(BaseModel):
    message: str
    verification_token: str | None = None


class PasswordResetRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=128)


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetTokenResponse(BaseModel):
    message: str
    reset_token: str | None = None
    expires_in_minutes: int


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=3, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminUserSummary(BaseModel):
    username: str
    email: str
    role: str
    display_name: str
    email_verified: bool
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    display_name: str | None = Field(default=None, max_length=64)

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class DeviceAuthRequest(BaseModel):
    device_id: str = Field(default="", max_length=64)


class DeviceAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    device_id: str


class TotpStatusResponse(BaseModel):
    eligible: bool
    enabled: bool
    pending_setup: bool


class TotpSetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class TotpEnableRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=8)


class TotpDisableRequest(BaseModel):
    password: str = Field(..., min_length=3, max_length=128)
    code: str = Field(..., min_length=6, max_length=8)


class TotpVerifyRequest(BaseModel):
    challenge_token: str = Field(..., min_length=8, max_length=512)
    code: str = Field(..., min_length=6, max_length=8)
