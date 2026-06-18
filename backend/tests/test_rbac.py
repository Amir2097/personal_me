"""Tests for terminal RBAC."""

from fastapi.testclient import TestClient


def test_projects_public_for_guest(client: TestClient):
    """Гость может смотреть публичные projects."""
    response = client.post("/api/v1/terminal/execute", json={"command": "projects"})
    assert response.status_code == 200
    body = response.json()
    assert body["requires_auth"] is False
    assert "personal-me" in body["output"]


def test_integrations_requires_admin(client: TestClient):
    """Обычный пользователь не может выполнить integrations."""
    register = client.post(
        "/api/v1/auth/register",
        json={"username": "rbac_user", "password": "rbacuser1"},
    )
    assert register.status_code == 201
    token = register.json()["access_token"]

    response = client.post(
        "/api/v1/terminal/execute",
        json={"command": "integrations"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["forbidden"] is True
    assert "прав" in body["output"]


def test_integrations_allowed_for_admin(client: TestClient):
    """Администратор видит полный список integrations."""
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/terminal/execute",
        json={"command": "integrations"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["forbidden"] is False
    assert "Все интеграции" in body["output"]
    assert "github" in body["output"]


def test_auth_me_and_token_is_admin(client: TestClient):
    """Login и /me возвращают is_admin."""
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    body = login.json()
    assert body["is_admin"] is True
    assert body["username"] == "admin"

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["is_admin"] is True
