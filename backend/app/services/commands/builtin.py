"""Встроенные terminal-команды."""

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext
from app.services.commands.registry import register_handler


@register_handler()
def handle_help(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда help."""
    if ctx.normalized != "help":
        return None
    lines = [
        "Доступные команды: help, projects, project, services, go, login, register, logout,",
        "clear, reset-request, reset-password, password, whoami, pwd, session, theme",
        "Портфолио в браузере: /projects",
    ]
    if ctx.is_admin:
        lines.append("integrations — список всех интеграций (admin)")
        lines.append("Админ: /admin/integrations  /admin/projects")
    return TerminalCommandResponse(command=ctx.command, output="\n".join(lines))


@register_handler()
def handle_clear(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда clear."""
    if ctx.normalized != "clear":
        return None
    return TerminalCommandResponse(command=ctx.command, output="__CLEAR__")


@register_handler()
def handle_auth_hints(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Подсказки для auth-команд."""
    hints = {
        "login": "Используйте команду login (откроется форма входа)",
        "register": "Используйте команду register (откроется форма регистрации)",
        "logout": "Используйте команду logout в терминале.",
        "reset-request": "Используйте: reset-request <логин>",
        "reset-password": "Используйте: reset-password <токен> <новый_пароль>",
        "password": "Используйте: password <текущий_пароль> <новый_пароль> (требуется авторизация)",
    }
    if ctx.normalized not in hints:
        return None
    return TerminalCommandResponse(command=ctx.command, output=hints[ctx.normalized])
