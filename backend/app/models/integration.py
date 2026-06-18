"""External service integration model."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Integration(SQLModel, table=True):
    """Внешний сервис для команд go/services."""

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True, nullable=False)
    url: str = Field(nullable=False)
    label: str = Field(default="", nullable=False)
    requires_auth: bool = Field(default=False, nullable=False)
    enabled: bool = Field(default=True, nullable=False)
    use_sso: bool = Field(default=False, nullable=False)
    sort_order: int = Field(default=0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
