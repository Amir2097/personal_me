"""User model."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Application user."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str | None = Field(default=None, index=True, unique=True)
    display_name: str = Field(default="", nullable=False)
    avatar_url: str = Field(default="", nullable=False)
    bio: str = Field(default="", nullable=False)
    location: str = Field(default="", nullable=False)
    website: str = Field(default="", nullable=False)
    telegram: str = Field(default="", nullable=False)
    github: str = Field(default="", nullable=False)
    hashed_password: str = Field(nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
    role: str = Field(default="user", nullable=False, index=True)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login_at: datetime | None = Field(default=None, nullable=True)
