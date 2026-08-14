"""Saved Cup tournament snapshots per hub user."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class CupTournament(SQLModel, table=True):
    """Сохранённый турнир (сетка) в истории пользователя."""

    id: int | None = Field(default=None, primary_key=True)
    owner_username: str = Field(index=True, nullable=False)
    title: str = Field(default="", max_length=200, nullable=False)
    format: str = Field(default="se", max_length=16, nullable=False)
    player_count: int = Field(default=0, nullable=False)
    winner_name: str = Field(default="", max_length=120, nullable=False)
    status: str = Field(default="completed", max_length=32, nullable=False)
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
