"""Cup multi-device sync service."""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.cup_session import CupSession
from app.services.sync_room_common import (
    generate_room_code,
    is_room_expired,
    new_room_expires_at,
)


def _expire_if_needed(session: Session, row: CupSession) -> None:
    if not is_room_expired(row.expires_at):
        return
    session.delete(row)
    session.commit()
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Комната не найдена.",
    )


def create_session(session: Session, owner_username: str) -> CupSession:
    for _ in range(12):
        code = generate_room_code()
        exists = session.exec(select(CupSession).where(CupSession.code == code)).first()
        if exists:
            continue
        row = CupSession(
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


def get_session_by_code(session: Session, code: str) -> CupSession:
    normalized = code.strip().upper()
    row = session.exec(select(CupSession).where(CupSession.code == normalized)).first()
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
) -> CupSession:
    del base_revision
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
    row = get_session_by_code(session, code)
    if row.owner_username != owner_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только создатель комнаты может завершить встречу.",
        )
    session.delete(row)
    session.commit()
