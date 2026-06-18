"""Integration API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class IntegrationCreate(BaseModel):
    """Создание интеграции."""

    key: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=1)
    label: str = ""
    requires_auth: bool = False
    use_sso: bool = False
    enabled: bool = True
    sort_order: int = 0


class IntegrationUpdate(BaseModel):
    """Частичное обновление интеграции."""

    url: str | None = None
    label: str | None = None
    requires_auth: bool | None = None
    use_sso: bool | None = None
    enabled: bool | None = None
    sort_order: int | None = None


class IntegrationRead(BaseModel):
    """Интеграция в ответе API."""

    id: int
    key: str
    url: str
    label: str
    requires_auth: bool
    use_sso: bool
    enabled: bool
    sort_order: int
    created_at: datetime
