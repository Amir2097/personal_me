"""Kolkhoz TV rooms."""

from tests.conftest import auth_headers


def test_session_sync_flow(client):
    headers = auth_headers(client)
    created = client.post("/api/v1/kolkhoz/sessions", headers=headers)
    assert created.status_code == 200
    code = created.json()["code"]
    pushed = client.put(
        f"/api/v1/kolkhoz/sessions/{code}",
        headers=headers,
        json={"state": {"version": 1, "mode": "tournament", "players": [], "events": []}},
    )
    assert pushed.status_code == 200
    fetched = client.get(f"/api/v1/kolkhoz/sessions/{code}")
    assert fetched.status_code == 200
    assert fetched.json()["state"]["mode"] == "tournament"
    assert client.delete(f"/api/v1/kolkhoz/sessions/{code}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/kolkhoz/sessions/{code}").status_code == 404


def test_create_requires_auth(client):
    assert client.post("/api/v1/kolkhoz/sessions").status_code == 401
