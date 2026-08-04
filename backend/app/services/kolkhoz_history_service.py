"""Service for saving Kolkhoz game history."""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, col, select

from app.models.kolkhoz_game import KolkhozGame


def _bank_total(state: dict[str, Any]) -> int:
    tournament = state.get("tournament") if isinstance(state.get("tournament"), dict) else {}
    buy_ins = tournament.get("buyIns") if isinstance(tournament, dict) else None
    if not isinstance(buy_ins, list):
        return 0
    total = 0
    for item in buy_ins:
        if isinstance(item, dict):
            try:
                total += int(item.get("money") or 0)
            except (TypeError, ValueError):
                continue
    return total


def _summarize(state: dict[str, Any]) -> dict[str, Any]:
    players = state.get("players") if isinstance(state.get("players"), list) else []
    events = state.get("events") if isinstance(state.get("events"), list) else []
    mode = str(state.get("mode") or "tournament")
    tournament = state.get("tournament") if isinstance(state.get("tournament"), dict) else {}
    kind = str(tournament.get("kind") or "") if mode == "tournament" else ""
    return {
        "mode": mode,
        "tournament_kind": kind,
        "player_count": len(players),
        "event_count": len(events),
        "bank_total": _bank_total(state),
    }


def save_game(
    session: Session,
    owner_username: str,
    state: dict[str, Any],
    title: str = "",
) -> KolkhozGame:
    """Persist a full game snapshot for the user."""
    if not isinstance(state, dict) or state.get("version") != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нужен state версии 1 (Kolkhoz).",
        )
    meta = _summarize(state)
    clean_title = (title or "").strip()
    if not clean_title:
        mode = meta["mode"]
        kind = meta["tournament_kind"]
        stamp = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
        if mode == "casual":
            clean_title = f"Быстрый стол · {stamp}"
        elif kind == "organizer":
            clean_title = f"Организаторская · {stamp}"
        else:
            clean_title = f"Подробная игра · {stamp}"

    row = KolkhozGame(
        owner_username=owner_username,
        title=clean_title[:200],
        mode=meta["mode"],
        tournament_kind=meta["tournament_kind"],
        player_count=meta["player_count"],
        event_count=meta["event_count"],
        bank_total=meta["bank_total"],
        state_json=state,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_games(session: Session, owner_username: str, limit: int = 50) -> list[KolkhozGame]:
    """List recent games for the user (newest first)."""
    limit = max(1, min(100, limit))
    return list(
        session.exec(
            select(KolkhozGame)
            .where(KolkhozGame.owner_username == owner_username)
            .order_by(col(KolkhozGame.created_at).desc())
            .limit(limit)
        ).all()
    )


def get_game(session: Session, game_id: int, owner_username: str) -> KolkhozGame:
    """Load one owned game."""
    row = session.get(KolkhozGame, game_id)
    if not row or row.owner_username != owner_username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена.")
    return row


def delete_game(session: Session, game_id: int, owner_username: str) -> None:
    """Delete owned game."""
    row = get_game(session, game_id, owner_username)
    session.delete(row)
    session.commit()
