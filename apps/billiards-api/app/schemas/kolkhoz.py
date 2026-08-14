"""Schemas for Kolkhoz multi-device sync sessions."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KolkhozSessionCreateResponse(BaseModel):
    """Созданная комната синхронизации."""

    code: str
    revision: int = 1
    tv_path: str = "/billiards/tv"


class KolkhozSessionPushRequest(BaseModel):
    """Пуш состояния партии с хоста."""

    state: dict[str, Any] = Field(default_factory=dict)
    # Optional client revision (informational; server uses last-write-wins).
    base_revision: int | None = None


class KolkhozSessionPushResponse(BaseModel):
    """Результат пуша."""

    code: str
    revision: int
    updated_at: datetime


class KolkhozSessionGetResponse(BaseModel):
    """Состояние комнаты для TV / подписчиков."""

    code: str
    revision: int
    updated_at: datetime
    owner_username: str
    state: dict[str, Any]


class KolkhozGameSaveRequest(BaseModel):
    """Сохранить снимок партии в историю."""

    state: dict[str, Any] = Field(default_factory=dict)
    title: str = ""


class KolkhozGameSummary(BaseModel):
    """Краткая карточка сохранённой партии."""

    id: int
    title: str
    mode: str
    tournament_kind: str
    player_count: int
    event_count: int
    bank_total: int
    created_at: datetime
    updated_at: datetime


class KolkhozGameDetail(KolkhozGameSummary):
    """Полная партия со state."""

    state: dict[str, Any]
    owner_username: str
