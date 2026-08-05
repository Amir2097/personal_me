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


def _default_title(state: dict[str, Any], meta: dict[str, Any]) -> str:
    stamp = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
    mode = meta["mode"]
    kind = meta["tournament_kind"]
    tournament = state.get("tournament") if isinstance(state.get("tournament"), dict) else {}
    rounds = tournament.get("rounds") if isinstance(tournament.get("rounds"), list) else []
    round_index = tournament.get("currentRoundIndex")
    round_label = ""
    if mode == "tournament" and isinstance(round_index, int) and rounds:
        number = rounds[round_index].get("number") if isinstance(rounds[round_index], dict) else None
        if number:
            round_label = f" · тур {number}"
    players = state.get("players") if isinstance(state.get("players"), list) else []
    eliminated = sum(1 for p in players if isinstance(p, dict) and p.get("status") == "eliminated")
    bank = meta["bank_total"]
    extras = []
    if bank:
        extras.append(f"банк {bank} ₽")
    if eliminated:
        extras.append(f"выбыло {eliminated}")
    extras_label = f" · {', '.join(extras)}" if extras else ""

    if mode == "casual":
        return f"Быстрый стол{extras_label} · {stamp}"
    if kind == "organizer":
        return f"Организаторская{round_label}{extras_label} · {stamp}"
    if kind == "detailed":
        return f"Подробная игра{round_label}{extras_label} · {stamp}"
    return f"Турнир{round_label}{extras_label} · {stamp}"


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
    clean_title = (title or "").strip() or _default_title(state, meta)

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


def update_game(
    session: Session,
    game_id: int,
    owner_username: str,
    state: dict[str, Any],
    title: str = "",
) -> KolkhozGame:
    """Overwrite an owned snapshot with the latest full state."""
    if not isinstance(state, dict) or state.get("version") != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нужен state версии 1 (Kolkhoz).",
        )
    row = get_game(session, game_id, owner_username)
    meta = _summarize(state)
    clean_title = (title or "").strip()
    row.title = (clean_title or _default_title(state, meta))[:200]
    row.mode = meta["mode"]
    row.tournament_kind = meta["tournament_kind"]
    row.player_count = meta["player_count"]
    row.event_count = meta["event_count"]
    row.bank_total = meta["bank_total"]
    row.state_json = state
    row.updated_at = datetime.now(timezone.utc)
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
