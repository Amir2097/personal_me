"""Service for saving Cup tournament history."""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, col, select

from app.models.cup_tournament import CupTournament


def _winner_name(state: dict[str, Any]) -> str:
    tournament = state.get("tournament") or {}
    winner_id = tournament.get("winnerId")
    if not winner_id:
        return ""
    for player in state.get("players") or []:
        if isinstance(player, dict) and player.get("id") == winner_id:
            return str(player.get("name") or "")
    return ""


def save_tournament(
    session: Session,
    owner_username: str,
    state: dict[str, Any],
    title: str | None = None,
) -> CupTournament:
    if not isinstance(state, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="state must be an object")
    tournament = state.get("tournament") or {}
    players = state.get("players") or []
    row = CupTournament(
        owner_username=owner_username,
        title=(title or tournament.get("name") or "Турнир")[:200],
        format=str(tournament.get("format") or "se")[:16],
        player_count=len(players) if isinstance(players, list) else 0,
        winner_name=_winner_name(state)[:120],
        status=str(tournament.get("status") or "completed")[:32],
        state_json=state,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def update_tournament(
    session: Session,
    tournament_id: int,
    owner_username: str,
    state: dict[str, Any],
    title: str | None = None,
) -> CupTournament:
    row = get_tournament(session, tournament_id, owner_username)
    tournament = state.get("tournament") or {}
    players = state.get("players") or []
    row.title = (title or tournament.get("name") or row.title)[:200]
    row.format = str(tournament.get("format") or row.format)[:16]
    row.player_count = len(players) if isinstance(players, list) else row.player_count
    row.winner_name = _winner_name(state)[:120]
    row.status = str(tournament.get("status") or row.status)[:32]
    row.state_json = state
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_tournaments(session: Session, owner_username: str, limit: int = 50) -> list[CupTournament]:
    return list(
        session.exec(
            select(CupTournament)
            .where(CupTournament.owner_username == owner_username)
            .order_by(col(CupTournament.created_at).desc())
            .limit(limit)
        ).all()
    )


def get_tournament(session: Session, tournament_id: int, owner_username: str) -> CupTournament:
    row = session.get(CupTournament, tournament_id)
    if not row or row.owner_username != owner_username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Турнир не найден.")
    return row


def delete_tournament(session: Session, tournament_id: int, owner_username: str) -> None:
    row = get_tournament(session, tournament_id, owner_username)
    session.delete(row)
    session.commit()
