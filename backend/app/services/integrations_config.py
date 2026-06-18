"""Конфигурация внешних сервисов для команд go/services."""

import json
from typing import Any

from pydantic import BaseModel

from app.core.config import settings

DEFAULT_INTEGRATIONS: dict[str, dict[str, Any]] = {
    "github": {
        "url": "https://github.com",
        "requires_auth": False,
        "label": "GitHub",
    },
    "gitlab": {
        "url": "https://gitlab.com",
        "requires_auth": False,
        "label": "GitLab",
    },
    "grafana": {
        "url": "http://localhost:3001",
        "requires_auth": True,
        "use_sso": True,
        "label": "Grafana",
    },
    "swagger": {
        "url": "http://localhost/api/docs",
        "requires_auth": False,
        "label": "Swagger API",
    },
}


class ExternalService(BaseModel):
    """Описание внешнего сервиса."""

    url: str
    requires_auth: bool = False
    label: str = ""
    use_sso: bool = False


def merge_env_overrides(
    integrations: dict[str, ExternalService],
) -> dict[str, ExternalService]:
    """Наложить INTEGRATIONS_JSON поверх значений из БД."""
    if not settings.integrations_json.strip():
        return integrations

    merged: dict[str, ExternalService] = {key: value.model_copy() for key, value in integrations.items()}
    try:
        custom = json.loads(settings.integrations_json)
    except json.JSONDecodeError:
        return integrations

    if not isinstance(custom, dict):
        return integrations

    for key, value in custom.items():
        if not isinstance(value, dict) or not value.get("url"):
            continue
        normalized = key.lower()
        current = merged.get(normalized, ExternalService(url="", label=normalized))
        merged[normalized] = ExternalService(
            url=str(value.get("url", current.url)),
            requires_auth=bool(value.get("requires_auth", current.requires_auth)),
            label=str(value.get("label", current.label or normalized)),
            use_sso=bool(value.get("use_sso", current.use_sso)),
        )
    return {key: item for key, item in merged.items() if item.url}
