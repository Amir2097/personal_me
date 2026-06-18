"""Terminal command DTOs."""

from pydantic import BaseModel, Field


class TerminalCommandRequest(BaseModel):
    """Incoming terminal command."""

    command: str = Field(..., min_length=1, max_length=128)


class TerminalCommandResponse(BaseModel):
    """Terminal command execution result."""

    command: str
    output: str
    requires_auth: bool = False
    forbidden: bool = False
    action: str | None = None
    url: str | None = None
