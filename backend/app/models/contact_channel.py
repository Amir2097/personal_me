"""Public contact channel model."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class ContactChannel(SQLModel, table=True):
    """Канал связи (telegram, email, github и т.д.)."""

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True, nullable=False)
    label: str = Field(default="", nullable=False)
    value: str = Field(nullable=False)
    kind: str = Field(default="link", nullable=False)
    enabled: bool = Field(default=True, nullable=False)
    sort_order: int = Field(default=0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
