"""Tests for Kolkhoz game history API."""


def _login(client) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_save_list_load_delete_game(client):
    headers = _login(client)
    state = {
        "version": 1,
        "mode": "tournament",
        "players": [{"id": "a", "name": "A", "balance": 20, "status": "active"}],
        "events": [{"id": "e1"}],
        "tournament": {
            "kind": "detailed",
            "buyIns": [{"money": 500, "chips": 20}],
            "rounds": [],
            "tables": [],
        },
        "casual": {"balls": [], "baseUnit": 1},
        "updatedAt": "2026-01-01T00:00:00Z",
    }

    saved = client.post(
        "/api/v1/kolkhoz/games",
        headers=headers,
        json={"state": state, "title": "Тестовая партия"},
    )
    assert saved.status_code == 201
    body = saved.json()
    assert body["title"] == "Тестовая партия"
    assert body["player_count"] == 1
    assert body["event_count"] == 1
    assert body["bank_total"] == 500
    game_id = body["id"]

    listed = client.get("/api/v1/kolkhoz/games", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == game_id for item in listed.json())

    loaded = client.get(f"/api/v1/kolkhoz/games/{game_id}", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["state"]["mode"] == "tournament"

    deleted = client.delete(f"/api/v1/kolkhoz/games/{game_id}", headers=headers)
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/kolkhoz/games/{game_id}", headers=headers)
    assert missing.status_code == 404


def test_games_require_auth(client):
    assert client.get("/api/v1/kolkhoz/games").status_code == 401
    assert client.post("/api/v1/kolkhoz/games", json={"state": {"version": 1}}).status_code == 401
