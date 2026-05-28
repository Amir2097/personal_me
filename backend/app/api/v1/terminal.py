"""Terminal command endpoints."""

from fastapi import APIRouter, Depends
from fastapi import HTTPException

from jose import JWTError

from app.api.deps import get_current_username_from_token, oauth2_scheme
from app.schemas.terminal import TerminalCommandRequest, TerminalCommandResponse
from app.services.terminal_service import execute_terminal_command

router = APIRouter(prefix="/terminal", tags=["terminal"])


@router.post(
    "/execute",
    response_model=TerminalCommandResponse,
    summary="Execute terminal command",
    description=(
        "Parses a terminal-like command and returns textual output. "
        "Some commands (e.g. projects) require JWT authentication."
    ),
)
def execute_command(
    payload: TerminalCommandRequest,
    token: str | None = Depends(oauth2_scheme),
) -> TerminalCommandResponse:
    """Execute terminal command using optional auth token."""
    is_authenticated = False
    if token:
        try:
            get_current_username_from_token(token)
            is_authenticated = True
        except (JWTError, HTTPException):
            is_authenticated = False
    return execute_terminal_command(payload.command, is_authenticated=is_authenticated)
