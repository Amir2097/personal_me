"""Terminal contact command."""

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext
from app.services.commands.registry import register_handler
from app.services.contact_service import (
    format_contacts_terminal,
    get_contact_by_key,
    list_contacts,
    resolve_contact_href,
)


@register_handler()
def handle_contact(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда contact — список каналов связи."""
    if ctx.normalized != "contact" and not ctx.normalized.startswith("contact "):
        return None

    if not ctx.session:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Контакты недоступны: нет подключения к БД.",
        )

    if ctx.normalized == "contact":
        return TerminalCommandResponse(
            command=ctx.command,
            output=format_contacts_terminal(ctx.session),
        )

    key = ctx.parts[1].lower() if len(ctx.parts) > 1 else ""
    if not key:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Используйте: contact <key>. Список: contact",
        )

    channel = get_contact_by_key(ctx.session, key)
    if not channel or not channel.enabled:
        available = ", ".join(item.key for item in list_contacts(ctx.session)) or "—"
        return TerminalCommandResponse(
            command=ctx.command,
            output=f"Контакт '{key}' не найден. Доступно: {available}",
        )

    href = resolve_contact_href(channel)
    label = channel.label or channel.key
    if href:
        return TerminalCommandResponse(
            command=ctx.command,
            output=f"Открываю {label}...",
            action="open_url",
            url=href,
        )

    return TerminalCommandResponse(
        command=ctx.command,
        output=f"{label}: {channel.value}",
    )
