"""Admin user management service."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.admin_user import AdminUserRead, AdminUserStats, AdminUserUpdate
from app.services.auth_service import revoke_user_refresh_tokens


def _last_session_map(session: Session) -> dict[str, datetime]:
    rows = session.exec(
        select(
            RefreshToken.username,
            func.max(RefreshToken.created_at).label("last_session_at"),
        ).group_by(RefreshToken.username)
    ).all()
    return {username: last_session_at for username, last_session_at in rows}


def _to_read(user: User, last_session_at: datetime | None) -> AdminUserRead:
    return AdminUserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        last_session_at=last_session_at,
    )


def get_user_stats(session: Session) -> AdminUserStats:
    users = list(session.exec(select(User)).all())
    return AdminUserStats(
        total=len(users),
        active=sum(1 for user in users if user.is_active),
        banned=sum(1 for user in users if not user.is_active),
        admins=sum(1 for user in users if user.is_admin),
    )


def list_users(session: Session) -> list[AdminUserRead]:
    sessions = _last_session_map(session)
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    return [_to_read(user, sessions.get(user.username)) for user in users]


def _count_admins(session: Session) -> int:
    return len(
        session.exec(
            select(User).where(User.is_admin == True, User.is_active == True)  # noqa: E712
        ).all()
    )


def update_user(
    session: Session,
    user_id: int,
    payload: AdminUserUpdate,
    actor: User,
) -> AdminUserRead:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )

    if payload.is_active is False and user.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя заблокировать свой аккаунт.",
        )

    if payload.is_admin is False and user.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя снять права администратора у себя.",
        )

    if payload.is_admin is False and user.is_admin and _count_admins(session) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя снять права у последнего администратора.",
        )

    if payload.is_active is False and user.is_admin and _count_admins(session) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя заблокировать последнего администратора.",
        )

    if payload.is_active is not None:
        user.is_active = payload.is_active
        if not payload.is_active:
            revoke_user_refresh_tokens(session, user.username)

    if payload.is_admin is not None:
        user.is_admin = payload.is_admin

    session.add(user)
    session.commit()
    session.refresh(user)
    sessions = _last_session_map(session)
    return _to_read(user, sessions.get(user.username))


def revoke_user_sessions(session: Session, user_id: int) -> None:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )
    revoke_user_refresh_tokens(session, user.username)
