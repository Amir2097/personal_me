"""Terminal command endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError
from sqlmodel import Session

from app.api.deps import get_current_username_from_token, get_optional_access_token
from app.core.db import get_session
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
    session: Session = Depends(get_session),
    token: str | None = Depends(get_optional_access_token),
) -> TerminalCommandResponse:
    """Execute terminal command using optional auth token."""
    is_authenticated = False
    username: str | None = None
    if token:
        try:
            username = get_current_username_from_token(token)
            is_authenticated = True
        except (JWTError, HTTPException):
            is_authenticated = False
            username = None
    return execute_terminal_command(
        payload.command,
        session=session,
        is_authenticated=is_authenticated,
        username=username,
    )
