"""Refresh token persistence model."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    """Stored refresh token metadata."""

    id: int | None = Field(default=None, primary_key=True)
    jti: str = Field(index=True, unique=True, nullable=False)
    username: str = Field(index=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
