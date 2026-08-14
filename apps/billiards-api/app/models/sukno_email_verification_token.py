"""Email verification tokens for Sukno accounts."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SuknoEmailVerificationToken(SQLModel, table=True):
    __tablename__ = "sukno_email_verification_token"

    id: int | None = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True, nullable=False)
    username: str = Field(index=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
