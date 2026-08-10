"""Billiards academy progress API."""

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.api.deps import get_current_username
from app.core.db import get_session
from app.schemas.academy import (
    AcademyProgressBulkUpsert,
    AcademyProgressItem,
    AcademyProgressListResponse,
    AcademyProgressUpsert,
)
from app.services import academy_progress_service

router = APIRouter(prefix="/academy", tags=["academy"])


def _to_item(row) -> AcademyProgressItem:
    return AcademyProgressItem(
        exercise_id=row.exercise_id,
        made=row.made,
        attempts=row.attempts,
        updated_at=row.updated_at,
    )


@router.get(
    "/progress",
    response_model=AcademyProgressListResponse,
    summary="Список прогресса академии",
)
def get_academy_progress(
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> AcademyProgressListResponse:
    rows = academy_progress_service.list_progress(session, username)
    return AcademyProgressListResponse(items=[_to_item(row) for row in rows])


@router.put(
    "/progress",
    response_model=AcademyProgressListResponse,
    summary="Слить прогресс с клиента",
)
def put_academy_progress_bulk(
    payload: AcademyProgressBulkUpsert,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> AcademyProgressListResponse:
    items = [
        (item.exercise_id, item.made, item.attempts, item.updated_at) for item in payload.items
    ]
    rows = academy_progress_service.merge_progress(session, username, items)
    return AcademyProgressListResponse(items=[_to_item(row) for row in rows])


@router.put(
    "/progress/{exercise_id}",
    response_model=AcademyProgressItem,
    summary="Сохранить результат упражнения",
)
def put_academy_progress_one(
    exercise_id: str,
    payload: AcademyProgressUpsert,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> AcademyProgressItem:
    row = academy_progress_service.upsert_progress(
        session,
        username,
        exercise_id,
        payload.made,
        payload.attempts,
        payload.updated_at,
    )
    return _to_item(row)


@router.delete(
    "/progress/{exercise_id}",
    status_code=204,
    summary="Удалить прогресс упражнения",
)
def delete_academy_progress(
    exercise_id: str,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> Response:
    academy_progress_service.delete_progress(session, username, exercise_id)
    return Response(status_code=204)
