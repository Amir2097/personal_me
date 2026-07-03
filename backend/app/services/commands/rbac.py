"""RBAC для terminal-команд."""

from app.core.roles import TerminalRole, role_level
from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext

Role = TerminalRole


def role_denied_response(ctx: CommandContext, min_role: Role) -> TerminalCommandResponse:
    """Сформировать ответ при недостаточных правах."""
    if ctx.role == "guest" and min_role in ("user", "kent", "rodnulka", "customer", "admin"):
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
    return role_level(ctx.role) >= role_level(min_role)
