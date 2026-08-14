"""Cup rooms on the dedicated API."""

from tests.conftest import auth_headers


def test_cup_session_sync_flow(client):
    headers = auth_headers(client)
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
