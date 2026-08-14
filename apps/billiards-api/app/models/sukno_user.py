"""Sukno account model (separate from hub User)."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SuknoUser(SQLModel, table=True):
    __tablename__ = "sukno_user"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    display_name: str = Field(default="", nullable=False)
    avatar_url: str = Field(default="", nullable=False)
    bio: str = Field(default="", nullable=False)
    location: str = Field(default="", nullable=False)
    telegram: str = Field(default="", nullable=False)
    hashed_password: str = Field(nullable=False)
    role: str = Field(default="player", nullable=False, index=True)
    is_active: bool = Field(default=True, nullable=False)
    email_verified: bool = Field(default=False, nullable=False)
    totp_secret: str = Field(default="", nullable=False)
    totp_enabled: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login_at: datetime | None = Field(default=None, nullable=True)
