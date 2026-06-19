"""Admin user management schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class AdminUserStats(BaseModel):
    total: int
    active: int
    banned: int
    admins: int


class AdminUserRead(BaseModel):
    id: int
    username: str
    email: str | None
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
    last_session_at: datetime | None


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None


class AdminUserActionResponse(BaseModel):
    ok: bool = True
    message: str = Field(default="")
