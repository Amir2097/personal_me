"""Pair self-scoring on a live cup room."""

from app.core.config import settings
from tests.conftest import login_headers, operator_headers, register_and_verify_player

LIVE_STATE = {
    "version": 1,
    "tournament": {
        "id": "t1",
        "name": "Кубок",
        "format": "se",
        "raceTo": 2,
        "shotClockSec": 0,
        "status": "running",
        "createdAt": "2026-01-01T00:00:00Z",
        "completedAt": None,
        "winnerId": None,
    },
    "players": [
        {"id": "p1", "name": "Анна", "seed": 1, "username": ""},
        {"id": "p2", "name": "Борис", "seed": 2, "username": "pair_b"},
    ],
    "matches": [
        {
            "id": "m1",
            "roundKey": "final",
            "roundLabel": "Финал",
            "bracketSide": "final",
            "order": 1,
            "displayNo": 1,
            "playerAId": "p1",
            "playerBId": "p2",
            "tableNo": 1,
            "status": "ready",
            "framesA": 0,
            "framesB": 0,
            "ballsA": 0,
            "ballsB": 0,
            "winnerId": None,
            "nextMatchId": None,
            "nextSlot": None,
            "loserNextMatchId": None,
            "loserNextSlot": None,
        }
    ],
    "activeMatchId": "m1",
    "shotClock": {
        "remainingMs": 0,
        "running": False,
        "endsAt": None,
        "pausedRemainingMs": None,
    },
}


def _open_room(client) -> str:
    headers = operator_headers(client)
    created = client.post("/api/v1/cup/sessions", headers=headers)
    assert created.status_code == 200
    code = created.json()["code"]
    pushed = client.put(
        f"/api/v1/cup/sessions/{code}",
        headers=headers,
        json={"state": LIVE_STATE},
    )
    assert pushed.status_code == 200
    return code


def test_device_cannot_claim_or_score(client):
    from tests.conftest import auth_headers

    code = _open_room(client)
    headers = auth_headers(client)
    assert (
        client.post(
            f"/api/v1/cup/sessions/{code}/claim",
            headers=headers,
            json={"player_id": "p1"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/cup/sessions/{code}/events",
            headers=headers,
            json={"match_id": "m1", "action": "award_frame", "side": "A"},
        ).status_code
        == 403
    )


def test_player_claims_and_awards_frame(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    register_and_verify_player(client, "pair_a", "pair_a@localhost")
    code = _open_room(client)
    headers = login_headers(client, "pair_a", "Player123!")

    denied = client.post(
        f"/api/v1/cup/sessions/{code}/events",
        headers=headers,
        json={"match_id": "m1", "action": "award_frame", "side": "A"},
    )
    assert denied.status_code == 403

    claimed = client.post(
        f"/api/v1/cup/sessions/{code}/claim",
        headers=headers,
        json={"player_id": "p1"},
    )
    assert claimed.status_code == 200
    players = {row["id"]: row for row in claimed.json()["state"]["players"]}
    assert players["p1"]["username"] == "pair_a"

    scored = client.post(
        f"/api/v1/cup/sessions/{code}/events",
        headers=headers,
        json={"match_id": "m1", "action": "award_frame", "side": "A"},
    )
    assert scored.status_code == 200
    match = next(item for item in scored.json()["state"]["matches"] if item["id"] == "m1")
    assert match["framesA"] == 1
    assert match["status"] == "live"

    guest = client.get(f"/api/v1/cup/sessions/{code}")
    assert guest.json()["state"]["matches"][0]["framesA"] == 1


def test_linked_player_can_complete_match(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    register_and_verify_player(client, "pair_b", "pair_b@localhost")
    code = _open_room(client)
    headers = login_headers(client, "pair_b", "Player123!")

    done = client.post(
        f"/api/v1/cup/sessions/{code}/events",
        headers=headers,
        json={"match_id": "m1", "action": "complete", "winner_id": "p2"},
    )
    assert done.status_code == 200
    match = done.json()["state"]["matches"][0]
    assert match["status"] == "done"
    assert match["winnerId"] == "p2"
    assert done.json()["state"]["tournament"]["winnerId"] == "p2"


def test_other_player_cannot_claim_taken_slot(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    register_and_verify_player(client, "pair_a", "pair_a@localhost")
    register_and_verify_player(client, "intruder", "intruder@localhost")
    code = _open_room(client)
    login_headers_a = login_headers(client, "pair_a", "Player123!")
    assert (
        client.post(
            f"/api/v1/cup/sessions/{code}/claim",
            headers=login_headers_a,
            json={"player_id": "p1"},
        ).status_code
        == 200
    )
    other = login_headers(client, "intruder", "Player123!")
    taken = client.post(
        f"/api/v1/cup/sessions/{code}/claim",
        headers=other,
        json={"player_id": "p1"},
    )
    assert taken.status_code == 409
