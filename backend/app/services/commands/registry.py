"""Реестр обработчиков terminal-команд."""

from collections.abc import Callable

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext
from app.services.commands.rbac import Role, has_min_role, role_denied_response

CommandHandler = Callable[[CommandContext], TerminalCommandResponse | None]

_handlers: list[tuple[Role, CommandHandler]] = []


def register_handler(min_role: Role = "guest") -> Callable[[CommandHandler], CommandHandler]:
    """Зарегистрировать обработчик с минимальной ролью."""

    def decorator(handler: CommandHandler) -> CommandHandler:
        def wrapped(ctx: CommandContext) -> TerminalCommandResponse | None:
            result = handler(ctx)
            if result is None:
                return None
            if not has_min_role(ctx, min_role):
                return role_denied_response(ctx, min_role)
            return result

        _handlers.append((min_role, wrapped))
        return handler

    return decorator


def dispatch_command(ctx: CommandContext) -> TerminalCommandResponse:
    """Выполнить первый подходящий обработчик."""
    for _, handler in _handlers:
        result = handler(ctx)
        if result is not None:
            return result
    return TerminalCommandResponse(
        command=ctx.command,
        output=f"Неизвестная команда: {ctx.normalized}. Введите help.",
    )
