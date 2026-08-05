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


def test_update_game_snapshot(client):
    headers = _login(client)
    state = {
        "version": 1,
        "mode": "tournament",
        "players": [
            {"id": "a", "name": "A", "balance": 20, "status": "active"},
            {"id": "b", "name": "B", "balance": 0, "status": "eliminated"},
        ],
        "events": [],
        "tournament": {
            "kind": "organizer",
            "currentRoundIndex": 2,
            "rounds": [{"number": 1}, {"number": 2}, {"number": 3}],
            "buyIns": [{"money": 500}, {"money": 500}],
            "tables": [],
        },
        "casual": {"balls": [], "baseUnit": 1},
        "updatedAt": "2026-01-01T00:00:00Z",
    }
    saved = client.post("/api/v1/kolkhoz/games", headers=headers, json={"state": state})
    assert saved.status_code == 201
    game_id = saved.json()["id"]

    state["tournament"]["buyIns"].append({"money": 300})
    state["events"] = [{"id": "e1"}, {"id": "e2"}]
    updated = client.put(
        f"/api/v1/kolkhoz/games/{game_id}",
        headers=headers,
        json={"state": state},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["id"] == game_id
    assert body["event_count"] == 2
    assert body["bank_total"] == 1300
    assert "тур 3" in body["title"].lower()


def test_games_require_auth(client):
    assert client.get("/api/v1/kolkhoz/games").status_code == 401
    assert client.post("/api/v1/kolkhoz/games", json={"state": {"version": 1}}).status_code == 401
