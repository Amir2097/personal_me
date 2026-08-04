"""Smoke tests for Kolkhoz sync rooms."""


def test_kolkhoz_session_create_requires_auth(client):
    response = client.post("/api/v1/kolkhoz/sessions")
    assert response.status_code == 401


def test_kolkhoz_session_sync_flow(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/api/v1/kolkhoz/sessions", headers=headers)
    assert created.status_code == 200
    code = created.json()["code"]
    assert len(code) == 6

    payload = {
        "state": {
            "version": 1,
            "mode": "tournament",
            "players": [{"id": "a", "name": "A", "balance": 20}],
            "events": [],
        }
    }
    pushed = client.put(f"/api/v1/kolkhoz/sessions/{code}", headers=headers, json=payload)
    assert pushed.status_code == 200
    assert pushed.json()["revision"] == 2

    # TV reads without auth
    fetched = client.get(f"/api/v1/kolkhoz/sessions/{code}")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["code"] == code
    assert body["revision"] == 2
    assert body["state"]["mode"] == "tournament"
    assert body["owner_username"] == "admin"

    # Foreign user cannot push
    # Register may be disabled — use wrong bearer
    denied = client.put(
        f"/api/v1/kolkhoz/sessions/{code}",
        headers={"Authorization": "Bearer invalid"},
        json=payload,
    )
    assert denied.status_code == 401
