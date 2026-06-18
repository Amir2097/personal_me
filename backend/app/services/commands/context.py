"""Контекст выполнения terminal-команды."""

from dataclasses import dataclass, field

from sqlmodel import Session

from app.services.integrations_config import ExternalService


@dataclass
class CommandContext:
    """Данные, доступные обработчикам команд."""

    command: str
    normalized: str
    parts: list[str]
    is_authenticated: bool
    username: str | None = None
    is_admin: bool = False
    session: Session | None = None
    integrations: dict[str, ExternalService] = field(default_factory=dict)
