"""Site-related terminal commands."""

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext
from app.services.commands.man_pages import MAN_PAGES
from app.services.commands.registry import register_handler
from app.services.site_service import (
    format_about_terminal,
    format_status_terminal,
    get_system_status,
)


@register_handler()
def handle_about(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда about."""
    if ctx.normalized != "about":
        return None
    return TerminalCommandResponse(command=ctx.command, output=format_about_terminal(ctx.session))


@register_handler()
def handle_status(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда status — health компонентов."""
    if ctx.normalized != "status":
        return None
    status = get_system_status(ctx.session)
    return TerminalCommandResponse(command=ctx.command, output=format_status_terminal(status))


@register_handler()
def handle_man(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда man <command>."""
    if not ctx.normalized.startswith("man"):
        return None
    if ctx.normalized == "man":
        return TerminalCommandResponse(
            command=ctx.command,
            output="Используйте: man <command>. Пример: man go",
        )
    target = ctx.parts[1].lower() if len(ctx.parts) > 1 else ""
    if not target:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Используйте: man <command>",
        )
    page = MAN_PAGES.get(target)
    if not page:
        return TerminalCommandResponse(
            command=ctx.command,
            output=f"Нет man-страницы для '{target}'. Введите help.",
        )
    return TerminalCommandResponse(command=ctx.command, output=page)
