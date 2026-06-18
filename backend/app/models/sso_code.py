"""One-time SSO code model."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SsoCode(SQLModel, table=True):
    """Одноразовый код для входа на внешний сервис."""

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, nullable=False)
    username: str = Field(index=True, nullable=False)
    service_key: str = Field(index=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
