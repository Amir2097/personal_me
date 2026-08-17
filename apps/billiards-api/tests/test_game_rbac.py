"""RBAC on kolkhoz/cup sync and per-user history."""

from app.core.config import settings
from tests.conftest import (
    auth_headers,
    login_headers,
    register_and_verify_player,
    verify_player,
)


def test_device_cannot_sync_kolkhoz(client):
    headers = auth_headers(client)
    assert client.post("/api/v1/kolkhoz/sessions", headers=headers).status_code == 403


def test_can_sync_room_matrix():
    from app.core.roles import can_sync_room

    assert not can_sync_room("device", None)
    assert not can_sync_room("hub", None)
    assert can_sync_room("legacy_admin", "admin")
    assert not can_sync_room("account", "player")
    assert can_sync_room("account", "operator")
    assert can_sync_room("account", "admin")


def test_guest_can_read_kolkhoz_session_without_auth(client):
    admin_headers = login_headers(
        client,
        settings.initial_admin_username,
        settings.initial_admin_password,
    )
    created = client.post("/api/v1/kolkhoz/sessions", headers=admin_headers)
    assert created.status_code == 200
    code = created.json()["code"]
    client.put(
        f"/api/v1/kolkhoz/sessions/{code}",
        headers=admin_headers,
        json={"state": {"version": 1, "mode": "casual", "players": [], "events": []}},
    )
    fetched = client.get(f"/api/v1/kolkhoz/sessions/{code}")
    assert fetched.status_code == 200
    assert fetched.json()["state"]["mode"] == "casual"


def test_player_account_cannot_sync_kolkhoz(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    reg = register_and_verify_player(client, "rbac_player", "rbac_player@localhost")
    headers = login_headers(client, "rbac_player", "Player123!")
    assert reg.status_code == 200
    denied = client.post("/api/v1/kolkhoz/sessions", headers=headers)
    assert denied.status_code == 403


def test_operator_account_can_sync_kolkhoz(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    register_and_verify_player(client, "rbac_operator", "rbac_operator@localhost")
    admin_headers = login_headers(client, settings.initial_admin_username, settings.initial_admin_password)
    promoted = client.patch(
        "/api/v1/site/admin/users/rbac_operator",
        headers=admin_headers,
        json={"role": "operator"},
    )
    assert promoted.status_code == 200
    op_headers = login_headers(client, "rbac_operator", "Player123!")
    assert client.post("/api/v1/kolkhoz/sessions", headers=op_headers).status_code == 200


def test_player_can_use_own_history_not_others(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    reg_a = register_and_verify_player(client, "hist_a", "hist_a@localhost")
    reg_b = register_and_verify_player(client, "hist_b", "hist_b@localhost")
    headers_a = login_headers(client, "hist_a", "Player123!")
    headers_b = login_headers(client, "hist_b", "Player123!")
    assert reg_a.status_code == 200
    assert reg_b.status_code == 200

    state = {
        "version": 1,
        "mode": "casual",
        "players": [],
        "events": [],
        "tournament": {"kind": "", "buyIns": [], "rounds": [], "tables": []},
        "casual": {"balls": [], "baseUnit": 1},
        "updatedAt": "2026-01-01T00:00:00Z",
    }
    saved = client.post(
        "/api/v1/kolkhoz/games",
        headers=headers_a,
        json={"state": state, "title": "A game"},
    )
    assert saved.status_code == 201
    game_id = saved.json()["id"]

    assert client.get(f"/api/v1/kolkhoz/games/{game_id}", headers=headers_a).status_code == 200
    assert client.get(f"/api/v1/kolkhoz/games/{game_id}", headers=headers_b).status_code == 404


def test_player_can_use_academy_progress(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    reg = register_and_verify_player(client, "academy_player", "academy_player@localhost")
    headers = login_headers(client, "academy_player", "Player123!")
    assert reg.status_code == 200
    upsert = client.put(
        "/api/v1/academy/progress/ex-1",
        headers=headers,
        json={"made": 3, "attempts": 5},
    )
    assert upsert.status_code == 200
    listed = client.get("/api/v1/academy/progress", headers=headers)
    assert listed.status_code == 200
    assert any(item["exercise_id"] == "ex-1" for item in listed.json()["items"])


def test_player_cannot_sync_cup(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    register_and_verify_player(client, "cup_player", "cup_player@localhost")
    headers = login_headers(client, "cup_player", "Player123!")
    assert client.post("/api/v1/cup/sessions", headers=headers).status_code == 403
