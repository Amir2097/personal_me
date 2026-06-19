"""Admin user management endpoints."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_admin_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.admin_user import (
    AdminUserActionResponse,
    AdminUserRead,
    AdminUserStats,
    AdminUserUpdate,
)
from app.services.user_admin_service import (
    get_user_stats,
    list_users,
    revoke_user_sessions,
    update_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/stats", response_model=AdminUserStats)
def read_user_stats(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> AdminUserStats:
    """Сводка по пользователям (admin)."""
    return get_user_stats(session)


@router.get("", response_model=list[AdminUserRead])
def read_users(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[AdminUserRead]:
    """Список пользователей (admin)."""
    return list_users(session)


@router.patch("/{user_id}", response_model=AdminUserRead)
def patch_user(
    user_id: int,
    payload: AdminUserUpdate,
    session: Session = Depends(get_session),
    actor: User = Depends(get_current_admin_user),
) -> AdminUserRead:
    """Обновить статус пользователя: ban/unban, admin (admin)."""
    return update_user(session, user_id, payload, actor)


@router.post("/{user_id}/revoke-sessions", response_model=AdminUserActionResponse)
def post_revoke_sessions(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> AdminUserActionResponse:
    """Отозвать все сессии пользователя (admin)."""
    revoke_user_sessions(session, user_id)
    return AdminUserActionResponse(message="Сессии пользователя отозваны.")
