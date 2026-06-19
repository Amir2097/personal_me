"""Admin user management API tests."""

from fastapi.testclient import TestClient


def _admin_client(client: TestClient) -> TestClient:
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    return client


def test_users_stats_requires_admin(client: TestClient):
    response = client.get("/api/v1/users/stats")
    assert response.status_code == 401


def test_users_stats_and_list(client: TestClient):
    client = _admin_client(client)
    stats = client.get("/api/v1/users/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["total"] >= 1
    assert body["admins"] >= 1

    users = client.get("/api/v1/users")
    assert users.status_code == 200
    items = users.json()
    assert len(items) >= 1
    admin = next(item for item in items if item["username"] == "admin")
    assert admin["is_admin"] is True
    assert admin["is_active"] is True


def test_ban_and_unban_user(client: TestClient):
    register = client.post(
        "/api/v1/auth/register",
        json={"username": "blocked_user", "password": "secret123", "accept_terms": True},
    )
    assert register.status_code in (200, 201)

    client = _admin_client(client)

    users = client.get("/api/v1/users")
    assert users.status_code == 200
    target = next(item for item in users.json() if item["username"] == "blocked_user")

    ban = client.patch(f"/api/v1/users/{target['id']}", json={"is_active": False})
    assert ban.status_code == 200
    assert ban.json()["is_active"] is False

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "blocked_user", "password": "secret123"},
    )
    assert login.status_code == 403

    unban = client.patch(f"/api/v1/users/{target['id']}", json={"is_active": True})
    assert unban.status_code == 200

    login_ok = client.post(
        "/api/v1/auth/login",
        json={"username": "blocked_user", "password": "secret123"},
    )
    assert login_ok.status_code == 200


def test_cannot_ban_self(client: TestClient):
    client = _admin_client(client)
    users = client.get("/api/v1/users").json()
    admin = next(item for item in users if item["username"] == "admin")
    response = client.patch(f"/api/v1/users/{admin['id']}", json={"is_active": False})
    assert response.status_code == 400
