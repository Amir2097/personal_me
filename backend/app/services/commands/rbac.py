"""RBAC для terminal-команд."""

from typing import Literal

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext

Role = Literal["guest", "user", "admin"]

_ROLE_LEVEL: dict[Role, int] = {"guest": 0, "user": 1, "admin": 2}


def role_level(ctx: CommandContext) -> int:
    """Уровень роли текущего пользователя в контексте команды."""
    if ctx.is_authenticated and ctx.is_admin:
        return _ROLE_LEVEL["admin"]
    if ctx.is_authenticated:
        return _ROLE_LEVEL["user"]
    return _ROLE_LEVEL["guest"]


def role_denied_response(ctx: CommandContext, min_role: Role) -> TerminalCommandResponse:
    """Сформировать ответ при недостаточных правах."""
    if role_level(ctx) < _ROLE_LEVEL["user"] and min_role in ("user", "admin"):
        return TerminalCommandResponse(
            command=ctx.command,
            output="Требуется авторизация. Сначала выполните login.",
            requires_auth=True,
        )
    return TerminalCommandResponse(
        command=ctx.command,
        output="Недостаточно прав для этой команды.",
        forbidden=True,
    )


def has_min_role(ctx: CommandContext, min_role: Role) -> bool:
    """Проверить, достаточно ли прав у пользователя."""
    return role_level(ctx) >= _ROLE_LEVEL[min_role]
