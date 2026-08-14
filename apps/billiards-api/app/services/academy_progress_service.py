"""Academy progress persistence per operator."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, col, select

from app.models.academy_progress import AcademyProgress


def _normalize(made: int, attempts: int) -> tuple[int, int]:
    clean_made = max(0, int(made))
    clean_attempts = max(1, int(attempts))
    return clean_made, clean_attempts


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def list_progress(session: Session, username: str) -> list[AcademyProgress]:
    statement = (
        select(AcademyProgress)
        .where(AcademyProgress.owner_username == username)
        .order_by(col(AcademyProgress.updated_at).desc())
    )
    return list(session.exec(statement).all())


def upsert_progress(
    session: Session,
    username: str,
    exercise_id: str,
    made: int,
    attempts: int,
    updated_at: datetime | None = None,
) -> AcademyProgress:
    exercise_id = exercise_id.strip()
    if not exercise_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="exercise_id required")

    made, attempts = _normalize(made, attempts)
    stamp = _as_utc(updated_at) if updated_at else datetime.now(timezone.utc)

    statement = select(AcademyProgress).where(
        AcademyProgress.owner_username == username,
        AcademyProgress.exercise_id == exercise_id,
    )
    row = session.exec(statement).first()
    if row is None:
        row = AcademyProgress(
            owner_username=username,
            exercise_id=exercise_id,
            made=made,
            attempts=attempts,
            updated_at=stamp,
        )
        session.add(row)
    else:
        # Keep the newer snapshot; ignore stale client writes.
        if _as_utc(row.updated_at) > stamp:
            return row
        row.made = made
        row.attempts = attempts
        row.updated_at = stamp
        session.add(row)

    session.commit()
    session.refresh(row)
    return row


def merge_progress(
    session: Session,
    username: str,
    items: list[tuple[str, int, int, datetime]],
) -> list[AcademyProgress]:
    """Upsert many entries; per exercise newer updated_at wins."""
    for exercise_id, made, attempts, updated_at in items:
        upsert_progress(session, username, exercise_id, made, attempts, updated_at)
    return list_progress(session, username)


def delete_progress(session: Session, username: str, exercise_id: str) -> None:
    statement = select(AcademyProgress).where(
        AcademyProgress.owner_username == username,
        AcademyProgress.exercise_id == exercise_id,
    )
    row = session.exec(statement).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found")
    session.delete(row)
    session.commit()
