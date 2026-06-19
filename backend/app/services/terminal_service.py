"""Terminal command execution logic."""

from sqlmodel import Session, select

from app.models.user import User
from app.schemas.terminal import TerminalCommandResponse
from app.services.commands import admin_commands, builtin, contact_commands, integrations, projects, site_commands  # noqa: F401
from app.services.commands.context import CommandContext
from app.services.commands.registry import dispatch_command
from app.services.integration_service import load_integrations


def execute_terminal_command(
    command: str,
    session: Session,
    is_authenticated: bool,
    username: str | None = None,
) -> TerminalCommandResponse:
    """Execute command through plugin registry."""
    is_admin = False
    if username:
        user = session.exec(select(User).where(User.username == username)).first()
        is_admin = bool(user and user.is_admin)

    normalized = command.strip().lower()
    parts = normalized.split()
    ctx = CommandContext(
        command=command,
        normalized=normalized,
        parts=parts,
        is_authenticated=is_authenticated,
        username=username,
        is_admin=is_admin,
        session=session,
        integrations=load_integrations(session),
    )
    return dispatch_command(ctx)
