"""Shared Kolkhoz game session for multi-device sync."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class KolkhozSession(SQLModel, table=True):
    """Комната синхронизации партии Колхоз (телефон ↔ TV)."""

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, max_length=8, nullable=False)
    owner_username: str = Field(index=True, nullable=False)
    state_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    revision: int = Field(default=1, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: datetime | None = Field(default=None, nullable=True)
