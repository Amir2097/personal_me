"""Cup bracket tournament sync + history API."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import get_current_username, require_account_actor, require_sync_actor
from app.core.db import get_session
from app.services import cup_history_service, cup_live_service, cup_sync_service

router = APIRouter(prefix="/cup", tags=["cup"])


class CupSessionCreateResponse(BaseModel):
    code: str
    revision: int


class CupSessionPushRequest(BaseModel):
    state: dict[str, Any] = Field(default_factory=dict)
    base_revision: int | None = None


class CupSessionPushResponse(BaseModel):
    code: str
    revision: int
    updated_at: datetime


class CupSessionGetResponse(BaseModel):
    code: str
    revision: int
    updated_at: datetime
    owner_username: str
    state: dict[str, Any]


class CupClaimRequest(BaseModel):
    player_id: str = Field(min_length=1)


class CupMatchEventRequest(BaseModel):
    match_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    side: str | None = None
    winner_id: str | None = None


class CupTournamentSaveRequest(BaseModel):
    state: dict[str, Any] = Field(default_factory=dict)
    title: str | None = None


class CupTournamentSummary(BaseModel):
    id: int
    title: str
    format: str
    player_count: int
    winner_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class CupTournamentDetail(CupTournamentSummary):
    state: dict[str, Any]


@router.post("/sessions", response_model=CupSessionCreateResponse, summary="Создать комнату турнира")
def create_cup_session(
    actor=Depends(require_sync_actor),
    session: Session = Depends(get_session),
) -> CupSessionCreateResponse:
    row = cup_sync_service.create_session(session, actor.username)
    return CupSessionCreateResponse(code=row.code, revision=row.revision)


@router.put("/sessions/{code}", response_model=CupSessionPushResponse, summary="Пуш состояния турнира")
def push_cup_session(
    code: str,
    payload: CupSessionPushRequest,
    actor=Depends(require_sync_actor),
    session: Session = Depends(get_session),
) -> CupSessionPushResponse:
    row = cup_sync_service.push_state(session, code, actor.username, payload.state, payload.base_revision)
    return CupSessionPushResponse(code=row.code, revision=row.revision, updated_at=row.updated_at)


@router.get("/sessions/{code}", response_model=CupSessionGetResponse, summary="Получить состояние турнира")
def get_cup_session(
    code: str,
    session: Session = Depends(get_session),
) -> CupSessionGetResponse:
    row = cup_sync_service.get_session_by_code(session, code)
    return CupSessionGetResponse(
        code=row.code,
        revision=row.revision,
        updated_at=row.updated_at,
        owner_username=row.owner_username,
        state=row.state_json or {},
    )


@router.delete("/sessions/{code}", status_code=204, summary="Закрыть комнату турнира")
def close_cup_session(
    code: str,
    actor=Depends(require_sync_actor),
    session: Session = Depends(get_session),
) -> Response:
    cup_sync_service.close_session(session, code, actor.username)
    return Response(status_code=204)


@router.post("/sessions/{code}/claim", response_model=CupSessionGetResponse, summary="Привязать себя к игроку сетки")
def claim_cup_player(
    code: str,
    payload: CupClaimRequest,
    actor=Depends(require_account_actor),
    session: Session = Depends(get_session),
) -> CupSessionGetResponse:
    row = cup_live_service.claim_player(session, code, actor, payload.player_id)
    return CupSessionGetResponse(
        code=row.code,
        revision=row.revision,
        updated_at=row.updated_at,
        owner_username=row.owner_username,
        state=row.state_json or {},
    )


@router.post("/sessions/{code}/events", response_model=CupSessionGetResponse, summary="Внести событие матча")
def apply_cup_match_event(
    code: str,
    payload: CupMatchEventRequest,
    actor=Depends(require_account_actor),
    session: Session = Depends(get_session),
) -> CupSessionGetResponse:
    row = cup_live_service.apply_match_event(
        session,
        code,
        actor,
        match_id=payload.match_id,
        action=payload.action.strip(),
        side=payload.side,
        winner_id=payload.winner_id,
    )
    return CupSessionGetResponse(
        code=row.code,
        revision=row.revision,
        updated_at=row.updated_at,
        owner_username=row.owner_username,
        state=row.state_json or {},
    )


def _to_summary(row) -> CupTournamentSummary:
    return CupTournamentSummary(
        id=row.id,
        title=row.title,
        format=row.format,
        player_count=row.player_count,
        winner_name=row.winner_name,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("/tournaments", response_model=CupTournamentSummary, summary="Сохранить турнир в историю")
def save_cup_tournament(
    payload: CupTournamentSaveRequest,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> CupTournamentSummary:
    row = cup_history_service.save_tournament(session, username, payload.state, payload.title)
    return _to_summary(row)


@router.get("/tournaments", response_model=list[CupTournamentSummary], summary="Список турниров")
def list_cup_tournaments(
    limit: int = Query(50, ge=1, le=100),
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> list[CupTournamentSummary]:
    rows = cup_history_service.list_tournaments(session, username, limit=limit)
    return [_to_summary(row) for row in rows]


@router.get("/tournaments/{tournament_id}", response_model=CupTournamentDetail, summary="Детали турнира")
def get_cup_tournament(
    tournament_id: int,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> CupTournamentDetail:
    row = cup_history_service.get_tournament(session, tournament_id, username)
    return CupTournamentDetail(
        **_to_summary(row).model_dump(),
        state=row.state_json or {},
    )


@router.put("/tournaments/{tournament_id}", response_model=CupTournamentSummary, summary="Обновить турнир в истории")
def update_cup_tournament(
    tournament_id: int,
    payload: CupTournamentSaveRequest,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> CupTournamentSummary:
    row = cup_history_service.update_tournament(
        session, tournament_id, username, payload.state, payload.title
    )
    return _to_summary(row)


@router.delete("/tournaments/{tournament_id}", status_code=204, summary="Удалить турнир из истории")
def delete_cup_tournament(
    tournament_id: int,
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> Response:
    cup_history_service.delete_tournament(session, tournament_id, username)
    return Response(status_code=204)
