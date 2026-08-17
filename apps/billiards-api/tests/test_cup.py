"""Cup rooms on the dedicated API."""

from tests.conftest import operator_headers


def test_cup_session_sync_flow(client):
    headers = operator_headers(client)
    created = client.post("/api/v1/cup/sessions", headers=headers)
    assert created.status_code == 200
    code = created.json()["code"]
    pushed = client.put(
        f"/api/v1/cup/sessions/{code}",
        headers=headers,
        json={"state": {"version": 1, "tournament": {"name": "Кубок"}}},
    )
    assert pushed.status_code == 200
    fetched = client.get(f"/api/v1/cup/sessions/{code}")
    assert fetched.status_code == 200
    assert fetched.json()["state"]["tournament"]["name"] == "Кубок"
    assert client.delete(f"/api/v1/cup/sessions/{code}", headers=headers).status_code == 204


def test_cup_tournament_history(client):
    headers = operator_headers(client)
    state = {
        "version": 1,
        "players": [{"id": "p1", "name": "Иван"}],
        "tournament": {"name": "Кубок весны", "format": "se", "status": "completed", "winnerId": "p1"},
    }
    saved = client.post(
        "/api/v1/cup/tournaments",
        headers=headers,
        json={"state": state, "title": "Кубок весны"},
    )
    assert saved.status_code == 200
    tournament_id = saved.json()["id"]
    listed = client.get("/api/v1/cup/tournaments", headers=headers)
    assert any(item["id"] == tournament_id for item in listed.json())
    loaded = client.get(f"/api/v1/cup/tournaments/{tournament_id}", headers=headers)
    assert loaded.json()["state"]["tournament"]["name"] == "Кубок весны"
    assert client.delete(f"/api/v1/cup/tournaments/{tournament_id}", headers=headers).status_code == 204


def test_cup_tournament_update(client):
    headers = operator_headers(client)
    state = {
        "version": 1,
        "players": [{"id": "p1", "name": "Иван"}],
        "tournament": {"name": "Кубок v1", "format": "se", "status": "completed", "winnerId": "p1"},
    }
    saved = client.post(
        "/api/v1/cup/tournaments",
        headers=headers,
        json={"state": state, "title": "Кубок v1"},
    )
    tournament_id = saved.json()["id"]
    state["tournament"]["name"] = "Кубок v2"
    updated = client.put(
        f"/api/v1/cup/tournaments/{tournament_id}",
        headers=headers,
        json={"state": state, "title": "Кубок v2"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Кубок v2"
    loaded = client.get(f"/api/v1/cup/tournaments/{tournament_id}", headers=headers)
    assert loaded.json()["state"]["tournament"]["name"] == "Кубок v2"


def test_guest_can_read_cup_session_without_auth(client):
    headers = operator_headers(client)
    created = client.post("/api/v1/cup/sessions", headers=headers)
    code = created.json()["code"]
    client.put(
        f"/api/v1/cup/sessions/{code}",
        headers=headers,
        json={"state": {"version": 1, "tournament": {"name": "Публичный"}}},
    )
    fetched = client.get(f"/api/v1/cup/sessions/{code}")
    assert fetched.status_code == 200
    assert fetched.json()["state"]["tournament"]["name"] == "Публичный"
