"""Refresh token persistence for Sukno accounts."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SuknoRefreshToken(SQLModel, table=True):
    __tablename__ = "sukno_refresh_token"

    id: int | None = Field(default=None, primary_key=True)
    jti: str = Field(index=True, unique=True, nullable=False)
    username: str = Field(index=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
