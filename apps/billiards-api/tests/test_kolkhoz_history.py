"""Kolkhoz history on the dedicated API."""

from tests.conftest import auth_headers


def test_save_list_load_delete_game(client):
    headers = auth_headers(client)
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
    game_id = saved.json()["id"]
    listed = client.get("/api/v1/kolkhoz/games", headers=headers)
    assert any(item["id"] == game_id for item in listed.json())
    loaded = client.get(f"/api/v1/kolkhoz/games/{game_id}", headers=headers)
    assert loaded.json()["state"]["mode"] == "tournament"
    assert client.delete(f"/api/v1/kolkhoz/games/{game_id}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/kolkhoz/games/{game_id}", headers=headers).status_code == 404


def test_games_require_auth(client):
    assert client.get("/api/v1/kolkhoz/games").status_code == 401
