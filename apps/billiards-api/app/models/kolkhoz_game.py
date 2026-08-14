"""Saved Kolkhoz game snapshots per hub user."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class KolkhozGame(SQLModel, table=True):
    """Сохранённая партия Колхоз (история пользователя)."""

    id: int | None = Field(default=None, primary_key=True)
    owner_username: str = Field(index=True, nullable=False)
    title: str = Field(default="", max_length=200, nullable=False)
    mode: str = Field(default="tournament", max_length=32, nullable=False)
    tournament_kind: str = Field(default="", max_length=32, nullable=False)
    player_count: int = Field(default=0, nullable=False)
    event_count: int = Field(default=0, nullable=False)
    bank_total: int = Field(default=0, nullable=False)
    state_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
