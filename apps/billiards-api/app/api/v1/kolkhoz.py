"""Kolkhoz multi-device sync + game history API."""

from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session

from app.api.deps import get_current_username, require_sync_actor
from app.core.db import get_session
from app.schemas.kolkhoz import (
    KolkhozGameDetail,
    KolkhozGameSaveRequest,
    KolkhozGameSummary,
    KolkhozSessionCreateResponse,
    KolkhozSessionGetResponse,
    KolkhozSessionPushRequest,
    KolkhozSessionPushResponse,
)
from app.services import kolkhoz_history_service, kolkhoz_sync_service

router = APIRouter(prefix="/kolkhoz", tags=["kolkhoz"])


@router.post(
    "/sessions",
    response_model=KolkhozSessionCreateResponse,
    summary="Создать комнату синхронизации",
)
def create_kolkhoz_session(
    actor=Depends(require_sync_actor),
    session: Session = Depends(get_session),
) -> KolkhozSessionCreateResponse:
    """Хост (телефон) создаёт код для TV."""
    row = kolkhoz_sync_service.create_session(session, actor.username)
    return KolkhozSessionCreateResponse(code=row.code, revision=row.revision)


@router.put(
    "/sessions/{code}",
    response_model=KolkhozSessionPushResponse,
    summary="Отправить состояние партии",
)
def push_kolkhoz_session(
    code: str,
    payload: KolkhozSessionPushRequest,
    actor=Depends(require_sync_actor),
    session: Session = Depends(get_session),
) -> KolkhozSessionPushResponse:
    """Хост пушит полный JSON состояния Pinia."""
    row = kolkhoz_sync_service.push_state(session, code, actor.username, payload.state)
    return KolkhozSessionPushResponse(
        code=row.code,
        revision=row.revision,
        updated_at=row.updated_at,
    )


@router.get(
    "/sessions/{code}",
    response_model=KolkhozSessionGetResponse,
    summary="Получить состояние комнаты",
)
def get_kolkhoz_session(
    code: str,
    session: Session = Depends(get_session),
) -> KolkhozSessionGetResponse:
    """TV и зрители читают состояние по коду (без auth)."""
    row = kolkhoz_sync_service.get_session_by_code(session, code)
    return KolkhozSessionGetResponse(
        code=row.code,
        revision=row.revision,
        updated_at=row.updated_at,
        owner_username=row.owner_username,
        state=row.state_json or {},
    )


@router.delete(
    "/sessions/{code}",
    status_code=204,
    summary="Завершить комнату (встречу)",
)
def close_kolkhoz_session(
    code: str,
    actor=Depends(require_sync_actor),
    session: Session = Depends(get_session),
) -> Response:
    """Хост завершает трансляцию — код больше не действует."""
    kolkhoz_sync_service.close_session(session, code, actor.username)
    return Response(status_code=204)


def _to_summary(row) -> KolkhozGameSummary:
    return KolkhozGameSummary(
        id=row.id,
        title=row.title,
        mode=row.mode,
        tournament_kind=row.tournament_kind,
        player_count=row.player_count,
        event_count=row.event_count,
        bank_total=row.bank_total,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post(
    "/games",
    response_model=KolkhozGameSummary,
    status_code=201,
    summary="Сохранить партию в историю",
)
def save_kolkhoz_game(
    payload: KolkhozGameSaveRequest,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> KolkhozGameSummary:
    """Сохранить снимок текущей партии под текущим оператором."""
    row = kolkhoz_history_service.save_game(session, username, payload.state, payload.title)
    return _to_summary(row)


@router.put(
    "/games/{game_id}",
    response_model=KolkhozGameSummary,
    summary="Обновить сохранённую партию",
)
def update_kolkhoz_game(
    game_id: int,
    payload: KolkhozGameSaveRequest,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> KolkhozGameSummary:
    """Перезаписать снимок (туры, докупы, выбывшие и т.д.)."""
    row = kolkhoz_history_service.update_game(
        session, game_id, username, payload.state, payload.title
    )
    return _to_summary(row)


@router.get(
    "/games",
    response_model=list[KolkhozGameSummary],
    summary="Список сохранённых партий",
)
def list_kolkhoz_games(
    limit: int = Query(default=50, ge=1, le=100),
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> list[KolkhozGameSummary]:
    """История партий текущего пользователя."""
    rows = kolkhoz_history_service.list_games(session, username, limit=limit)
    return [_to_summary(row) for row in rows]


@router.get(
    "/games/{game_id}",
    response_model=KolkhozGameDetail,
    summary="Загрузить партию",
)
def get_kolkhoz_game(
    game_id: int,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> KolkhozGameDetail:
    """Полный state для восстановления на клиенте."""
    row = kolkhoz_history_service.get_game(session, game_id, username)
    return KolkhozGameDetail(
        **_to_summary(row).model_dump(),
        state=row.state_json or {},
        owner_username=row.owner_username,
    )


@router.delete(
    "/games/{game_id}",
    status_code=204,
    summary="Удалить партию из истории",
)
def delete_kolkhoz_game(
    game_id: int,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> Response:
    """Удалить свою сохранённую партию."""
    kolkhoz_history_service.delete_game(session, game_id, username)
    return Response(status_code=204)
