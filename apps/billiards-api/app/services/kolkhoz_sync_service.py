"""Kolkhoz multi-device sync service."""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.kolkhoz_session import KolkhozSession
from app.services.sync_room_common import (
    generate_room_code,
    is_room_expired,
    new_room_expires_at,
)


def _expire_if_needed(session: Session, row: KolkhozSession) -> None:
    if not is_room_expired(row.expires_at):
        return
    session.delete(row)
    session.commit()
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Комната не найдена.",
    )


def create_session(session: Session, owner_username: str) -> KolkhozSession:
    """Create a new sync room for the authenticated host."""
    for _ in range(12):
        code = generate_room_code()
        exists = session.exec(select(KolkhozSession).where(KolkhozSession.code == code)).first()
        if exists:
            continue
        row = KolkhozSession(
            code=code,
            owner_username=owner_username,
            state_json={},
            revision=1,
            expires_at=new_room_expires_at(),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Не удалось создать код комнаты.",
    )


def get_session_by_code(session: Session, code: str) -> KolkhozSession:
    """Load room by code (case-insensitive)."""
    normalized = code.strip().upper()
    row = session.exec(select(KolkhozSession).where(KolkhozSession.code == normalized)).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комната не найдена.",
        )
    _expire_if_needed(session, row)
    return row


def push_state(
    session: Session,
    code: str,
    owner_username: str,
    state: dict[str, Any],
    base_revision: int | None = None,
) -> KolkhozSession:
    """Host pushes full game state (last-write-wins)."""
    del base_revision  # informational from client; server increments revision
    row = get_session_by_code(session, code)
    if row.owner_username != owner_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только создатель комнаты может обновлять состояние.",
        )
    if not isinstance(state, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="state must be an object.",
        )
    row.state_json = state
    row.revision = int(row.revision or 0) + 1
    row.updated_at = datetime.now(timezone.utc)
    row.expires_at = new_room_expires_at()
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def close_session(session: Session, code: str, owner_username: str) -> None:
    """Host ends the meeting — room code stops working for TVs."""
    row = get_session_by_code(session, code)
    if row.owner_username != owner_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только создатель комнаты может завершить встречу.",
        )
    session.delete(row)
    session.commit()
