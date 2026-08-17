"""Apply cup match scoring to synced tournament state (pair self-report)."""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.core.roles import can_sync_room
from app.services import cup_sync_service
from app.services.sync_room_common import new_room_expires_at


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _players(state: dict[str, Any]) -> list[dict[str, Any]]:
    players = state.get("players")
    return players if isinstance(players, list) else []


def _matches(state: dict[str, Any]) -> list[dict[str, Any]]:
    matches = state.get("matches")
    return matches if isinstance(matches, list) else []


def _player_by_id(state: dict[str, Any], player_id: str | None) -> dict[str, Any] | None:
    if not player_id:
        return None
    for player in _players(state):
        if isinstance(player, dict) and player.get("id") == player_id:
            return player
    return None


def _match_by_id(state: dict[str, Any], match_id: str) -> dict[str, Any] | None:
    for match in _matches(state):
        if isinstance(match, dict) and match.get("id") == match_id:
            return match
    return None


def actor_linked_to_match(actor_username: str, state: dict[str, Any], match: dict[str, Any]) -> bool:
    mine = _norm(actor_username)
    if not mine:
        return False
    for key in ("playerAId", "playerBId"):
        player = _player_by_id(state, match.get(key) if isinstance(match.get(key), str) else None)
        if player and _norm(str(player.get("username") or "")) == mine:
            return True
    return False


def _assert_can_score(actor, state: dict[str, Any], match: dict[str, Any]) -> None:
    if can_sync_room(actor.source, actor.role):
        return
    if actor_linked_to_match(actor.username, state, match):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Вносить счёт могут участники этой пары (привязанный аккаунт) или оператор.",
    )


def _place_player(
    matches: list[dict[str, Any]],
    match_id: str | None,
    slot: str | None,
    player_id: str,
) -> None:
    if not match_id or not slot:
        return
    match = next((item for item in matches if item.get("id") == match_id), None)
    if not match:
        return
    if slot == "A":
        match["playerAId"] = player_id
    else:
        match["playerBId"] = player_id
    if match.get("playerAId") and match.get("playerBId") and match.get("status") == "pending":
        match["status"] = "ready"


def _slot_still_fed(matches: list[dict[str, Any]], match_id: str, slot: str) -> bool:
    for match in matches:
        if match.get("status") == "done":
            continue
        if match.get("nextMatchId") == match_id and match.get("nextSlot") == slot:
            return True
        if match.get("loserNextMatchId") == match_id and match.get("loserNextSlot") == slot:
            return True
    return False


def _resolve_single_player_byes(matches: list[dict[str, Any]]) -> None:
    changed = True
    while changed:
        changed = False
        for match in matches:
            if match.get("status") == "done":
                continue
            has_a = bool(match.get("playerAId"))
            has_b = bool(match.get("playerBId"))
            if has_a == has_b:
                continue
            if has_a and _slot_still_fed(matches, match["id"], "B"):
                continue
            if has_b and _slot_still_fed(matches, match["id"], "A"):
                continue
            winner_id = match.get("playerAId") or match.get("playerBId")
            if not match.get("playerAId") and match.get("playerBId"):
                match["playerAId"] = match["playerBId"]
                match["playerBId"] = None
            match["winnerId"] = winner_id
            match["status"] = "done"
            _place_player(matches, match.get("nextMatchId"), match.get("nextSlot"), winner_id)
            changed = True


def advance_winner(
    matches_input: list[dict[str, Any]],
    match_id: str,
    winner_id: str,
    fmt: str,
) -> tuple[list[dict[str, Any]], str | None, bool]:
    matches = deepcopy(matches_input)
    match = next((item for item in matches if item.get("id") == match_id), None)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матч не найден.")
    if match.get("status") == "done":
        return matches, None, False
    if winner_id not in (match.get("playerAId"), match.get("playerBId")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Победитель должен быть участником матча.",
        )

    loser_id = match.get("playerBId") if winner_id == match.get("playerAId") else match.get("playerAId")
    match["winnerId"] = winner_id
    match["status"] = "done"
    match["ballsA"] = 0
    match["ballsB"] = 0
    _place_player(matches, match.get("nextMatchId"), match.get("nextSlot"), winner_id)
    if fmt == "de" and loser_id:
        _place_player(matches, match.get("loserNextMatchId"), match.get("loserNextSlot"), loser_id)
    _resolve_single_player_byes(matches)

    round_key = match.get("roundKey")
    completed = False
    tournament_winner_id = None
    if round_key in ("de-final", "grand-final") or (fmt == "se" and match.get("bracketSide") == "final"):
        tournament_winner_id = winner_id
        completed = True
    elif fmt == "se" and not match.get("nextMatchId"):
        tournament_winner_id = winner_id
        completed = True
    return matches, tournament_winner_id, completed


def _mark_live(match: dict[str, Any]) -> None:
    if match.get("status") in ("pending", "ready"):
        match["status"] = "live"


def _persist(session, row, state: dict[str, Any]):
    row.state_json = state
    row.revision = int(row.revision or 0) + 1
    row.updated_at = datetime.now(timezone.utc)
    row.expires_at = new_room_expires_at()
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def claim_player(session, code: str, actor, player_id: str):
    row = cup_sync_service.get_session_by_code(session, code)
    state = deepcopy(row.state_json or {})
    player = _player_by_id(state, player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Игрок не найден.")

    mine = actor.username.strip()
    current = str(player.get("username") or "").strip()
    if current and _norm(current) != _norm(mine):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот слот уже привязан к другому аккаунту.",
        )
    for other in _players(state):
        if other.get("id") == player_id:
            continue
        if _norm(str(other.get("username") or "")) == _norm(mine):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Этот аккаунт уже привязан к другому участнику.",
            )
    player["username"] = mine
    return _persist(session, row, state)


def apply_match_event(
    session,
    code: str,
    actor,
    *,
    match_id: str,
    action: str,
    side: str | None = None,
    winner_id: str | None = None,
):
    row = cup_sync_service.get_session_by_code(session, code)
    state = deepcopy(row.state_json or {})
    match = _match_by_id(state, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матч не найден.")
    _assert_can_score(actor, state, match)
    if match.get("status") == "done" and action != "complete":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Матч уже завершён.")

    tournament = state.get("tournament") if isinstance(state.get("tournament"), dict) else {}
    race_to = int(tournament.get("raceTo") or 1)
    fmt = str(tournament.get("format") or "se")

    if action == "add_ball":
        if side not in ("A", "B"):
            raise HTTPException(status_code=400, detail="Укажите сторону A или B.")
        _mark_live(match)
        key = "ballsA" if side == "A" else "ballsB"
        match[key] = int(match.get(key) or 0) + 1
    elif action == "undo_ball":
        if side not in ("A", "B"):
            raise HTTPException(status_code=400, detail="Укажите сторону A или B.")
        key = "ballsA" if side == "A" else "ballsB"
        match[key] = max(0, int(match.get(key) or 0) - 1)
    elif action == "award_frame":
        if side not in ("A", "B"):
            raise HTTPException(status_code=400, detail="Укажите сторону A или B.")
        _mark_live(match)
        if side == "A":
            match["framesA"] = int(match.get("framesA") or 0) + 1
        else:
            match["framesB"] = int(match.get("framesB") or 0) + 1
        match["ballsA"] = 0
        match["ballsB"] = 0
        frames_a = int(match["framesA"])
        frames_b = int(match["framesB"])
        auto_winner = None
        if frames_a >= race_to and match.get("playerAId"):
            auto_winner = match["playerAId"]
        elif frames_b >= race_to and match.get("playerBId"):
            auto_winner = match["playerBId"]
        if auto_winner:
            matches, winner, completed = advance_winner(_matches(state), match_id, auto_winner, fmt)
            state["matches"] = matches
            if completed and winner:
                tournament["status"] = "completed"
                tournament["winnerId"] = winner
                tournament["completedAt"] = datetime.now(timezone.utc).isoformat()
                state["tournament"] = tournament
    elif action == "complete":
        chosen = winner_id or ""
        if not chosen:
            raise HTTPException(status_code=400, detail="Укажите победителя.")
        matches, winner, completed = advance_winner(_matches(state), match_id, chosen, fmt)
        state["matches"] = matches
        if completed and winner:
            tournament["status"] = "completed"
            tournament["winnerId"] = winner
            tournament["completedAt"] = datetime.now(timezone.utc).isoformat()
            state["tournament"] = tournament
    else:
        raise HTTPException(status_code=400, detail="Неизвестное действие.")

    return _persist(session, row, state)
