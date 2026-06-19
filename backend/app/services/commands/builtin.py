"""Встроенные terminal-команды."""

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext
from app.services.commands.registry import register_handler


def _help_lines(ctx: CommandContext) -> list[str]:
    lines = [
        "=== personal_me terminal help ===",
        "",
        "[general]",
        "  help, man <cmd>, about, status, clear",
        "  whoami, pwd, session, theme, fx, lang",
        "",
        "[portfolio]",
        "  projects, project <slug>     веб: /projects",
        "",
        "[services]",
        "  services, go <service>       открыть интеграцию",
        "",
        "[auth]",
        "  login, register, logout",
        "  profile                      веб: /profile",
        "  reset-request, reset-password, password",
        "",
        "[personal]",
        "  contact                      связаться (веб: /contact)",
        "  theme auto|green|amber|blue",
        "  fx preset retro|hacker|minimal",
        "  alias <name>=<cmd>          пользовательский алиас",
    ]
    if ctx.is_admin:
        lines.extend(
            [
                "",
                "[admin]",
                "  integrations",
                "  веб: /admin/integrations  /admin/projects  /admin/contacts  /admin/seo  /admin/users  /admin/oidc-clients",
            ]
        )
    lines.extend(["", "Подробнее: man <command>"])
    return lines


@register_handler()
def handle_help(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда help."""
    if ctx.normalized != "help":
        return None
    return TerminalCommandResponse(command=ctx.command, output="\n".join(_help_lines(ctx)))


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
        "profile": "Профиль: команда profile или откройте /profile",
        "reset-request": "Используйте: reset-request <логин>",
        "reset-password": "Используйте: reset-password <токен> <новый_пароль>",
        "password": "Используйте: password <текущий_пароль> <новый_пароль> (требуется авторизация)",
    }
    if ctx.normalized not in hints:
        return None
    return TerminalCommandResponse(command=ctx.command, output=hints[ctx.normalized])
