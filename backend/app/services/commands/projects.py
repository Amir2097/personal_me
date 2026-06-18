"""Terminal-команды портфолио."""

from fastapi import HTTPException

from app.schemas.terminal import TerminalCommandResponse
from app.services.commands.context import CommandContext
from app.services.commands.registry import register_handler
from app.services.project_service import (
    format_project_detail,
    format_projects_list,
    get_visible_project,
    list_projects,
)


def _include_private(ctx: CommandContext) -> bool:
    return ctx.is_authenticated


@register_handler()
def handle_projects(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда projects — список проектов."""
    if ctx.normalized != "projects":
        return None
    if ctx.session is None:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Внутренняя ошибка: сессия БД недоступна.",
        )
    projects = list_projects(ctx.session, include_private=_include_private(ctx))
    return TerminalCommandResponse(
        command=ctx.command,
        output=format_projects_list(projects),
    )


@register_handler()
def handle_project(ctx: CommandContext) -> TerminalCommandResponse | None:
    """Команда project <slug> — карточка проекта."""
    if not ctx.normalized.startswith("project "):
        return None
    if ctx.session is None:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Внутренняя ошибка: сессия БД недоступна.",
        )

    slug = ctx.parts[1] if len(ctx.parts) > 1 else ""
    if not slug:
        return TerminalCommandResponse(
            command=ctx.command,
            output="Используйте: project <slug>. Список: projects",
        )

    try:
        item = get_visible_project(ctx.session, slug, include_private=_include_private(ctx))
    except HTTPException:
        return TerminalCommandResponse(
            command=ctx.command,
            output=f"Проект '{slug}' не найден.",
        )

    return TerminalCommandResponse(
        command=ctx.command,
        output=format_project_detail(item),
    )
