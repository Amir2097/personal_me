"""Команды перехода к внешним сервисам (go / services)."""

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext
from app.services.commands.registry import register_handler
from app.services.sso_service import append_sso_code_to_url, create_sso_code


def _format_services_list(integrations: dict) -> str:
    """Сформировать список доступных сервисов."""
    if not integrations:
        return "Внешние сервисы не настроены."
    lines = ["Доступные сервисы:"]
    for key, service in sorted(integrations.items()):
        access = "auth" if service.requires_auth else "public"
        lines.append(f"  - {key}: {service.label} ({access}) -> {service.url}")
    lines.append("Используйте: go <сервис>")
    return "\n".join(lines)


@register_handler()
def handle_services(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда services — список интеграций."""
    if ctx.normalized not in {"services", "go", "go list"}:
        return None
    return TerminalCommandResponse(
        command=ctx.command,
        output=_format_services_list(ctx.integrations),
    )


@register_handler()
def handle_go(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда go <service> — открыть внешний сервис."""
    if not ctx.normalized.startswith("go "):
        return None
    if ctx.normalized in {"go list"}:
        return None

    service_key = ctx.parts[1].lower() if len(ctx.parts) > 1 else ""
    if not service_key:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Используйте: go <сервис>. Список: services",
        )

    integrations = ctx.integrations
    service = integrations.get(service_key)
    if not service:
        return TerminalCommandResponse(
            command=ctx.command,
            output=f"Сервис '{service_key}' не найден. Введите services.",
        )

    if service.requires_auth and not ctx.is_authenticated:
        return TerminalCommandResponse(
            command=ctx.command,
            output=f"Сервис '{service_key}' доступен только после login.",
            requires_auth=True,
        )

    target_url = service.url
    if service.use_sso and ctx.is_authenticated and ctx.session and ctx.username:
        code = create_sso_code(ctx.session, ctx.username, service_key)
        target_url = append_sso_code_to_url(service.url, code)

    return TerminalCommandResponse(
        command=ctx.command,
        output=f"Открываю {service.label}...",
        action="open_url",
        url=target_url,
    )
