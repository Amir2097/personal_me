"""Admin-only terminal-команды."""

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext
from app.services.commands.registry import register_handler
from app.services.integration_service import list_integrations


@register_handler("admin")
def handle_integrations_admin(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда integrations — полный список для администратора."""
    if ctx.normalized != "integrations":
        return None
    if ctx.session is None:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Внутренняя ошибка: сессия БД недоступна.",
        )

    rows = list_integrations(ctx.session, include_disabled=True)
    if not rows:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Интеграции не настроены. Используйте /admin/integrations.",
        )

    lines = ["Все интеграции (admin):"]
    for item in rows:
        status = "on" if item.enabled else "off"
        access = "auth" if item.requires_auth else "public"
        lines.append(
            f"  - [{status}] {item.key}: {item.label} ({access}) -> {item.url}"
        )
    lines.append("Управление: /admin/integrations")
    return TerminalCommandResponse(command=ctx.command, output="\n".join(lines))
