"""Terminal command execution logic."""

from app.schemas.terminal import TerminalCommandResponse

PUBLIC_COMMANDS = {"help", "clear", "login", "logout"}
PRIVATE_COMMANDS = {"projects"}


def execute_terminal_command(command: str, is_authenticated: bool) -> TerminalCommandResponse:
    """Execute command and return terminal-friendly output."""
    normalized = command.strip().lower()
    if normalized == "help":
        return TerminalCommandResponse(
            command=command,
            output="Available commands: help, login, register, logout, projects, clear",
        )
    if normalized == "clear":
        return TerminalCommandResponse(command=command, output="__CLEAR__")
    if normalized == "login":
        return TerminalCommandResponse(
            command=command,
            output="Use /api/v1/auth/login endpoint to receive JWT token.",
        )
    if normalized == "register":
        return TerminalCommandResponse(
            command=command,
            output="Use 'register <username> <password>' to create a user session.",
        )
    if normalized == "logout":
        return TerminalCommandResponse(
            command=command,
            output="Use /api/v1/auth/logout endpoint with refresh_token.",
        )
    if normalized == "projects":
        if not is_authenticated:
            return TerminalCommandResponse(
                command=command,
                output="Authentication required. Run login first.",
                requires_auth=True,
            )
        return TerminalCommandResponse(
            command=command,
            output="Projects: personal-me, cli-lab, infra-playground",
        )
    return TerminalCommandResponse(
        command=command,
        output=f"Unknown command: {normalized}. Type 'help'.",
    )
