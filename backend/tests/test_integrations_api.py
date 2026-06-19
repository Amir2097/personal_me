"""Tests for integrations admin CRUD API."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    """JWT заголовок администратора."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(client: TestClient) -> dict[str, str]:
    """JWT заголовок обычного пользователя."""
    register = client.post(
        "/api/v1/auth/register",
        json={"username": "regular", "password": "regular123", "accept_terms": True},
    )
    assert register.status_code == 201
    token = register.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_integrations_public(client: TestClient):
    """Публичный список включает сиды по умолчанию."""
    response = client.get("/api/v1/integrations")
    assert response.status_code == 200
    keys = {item["key"] for item in response.json()}
    assert "github" in keys
    assert "swagger" in keys


def test_integrations_admin_crud(client: TestClient, admin_headers: dict[str, str]):
    """Admin может создавать, обновлять и удалять интеграции."""
    create = client.post(
        "/api/v1/integrations",
        json={
            "key": "jira",
            "url": "https://jira.example.com",
            "label": "Jira",
            "requires_auth": True,
            "sort_order": 10,
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    created = create.json()
    assert created["key"] == "jira"
    integration_id = created["id"]

    listed = client.get("/api/v1/integrations")
    assert any(item["key"] == "jira" for item in listed.json())

    patch = client.patch(
        f"/api/v1/integrations/{integration_id}",
        json={"label": "Jira Cloud", "enabled": False},
        headers=admin_headers,
    )
    assert patch.status_code == 200
    assert patch.json()["label"] == "Jira Cloud"
    assert patch.json()["enabled"] is False

    public_after_disable = client.get("/api/v1/integrations")
    assert "jira" not in {item["key"] for item in public_after_disable.json()}

    all_items = client.get("/api/v1/integrations/all", headers=admin_headers)
    assert all_items.status_code == 200
    assert any(item["key"] == "jira" for item in all_items.json())

    delete = client.delete(
        f"/api/v1/integrations/{integration_id}",
        headers=admin_headers,
    )
    assert delete.status_code == 204

    missing = client.get(f"/api/v1/integrations/{integration_id}")
    assert missing.status_code == 404


def test_integrations_forbidden_for_regular_user(
    client: TestClient, user_headers: dict[str, str]
):
    """Обычный пользователь не может менять интеграции."""
    response = client.post(
        "/api/v1/integrations",
        json={"key": "hack", "url": "https://evil.example"},
        headers=user_headers,
    )
    assert response.status_code == 403


def test_terminal_reflects_db_integration(
    client: TestClient, admin_headers: dict[str, str]
):
    """Команда services видит интеграцию, добавленную через API."""
    create = client.post(
        "/api/v1/integrations",
        json={
            "key": "notion",
            "url": "https://notion.so",
            "label": "Notion",
            "requires_auth": False,
        },
        headers=admin_headers,
    )
    assert create.status_code == 201

    services = client.post("/api/v1/terminal/execute", json={"command": "services"})
    assert services.status_code == 200
    assert "notion" in services.json()["output"]

    go = client.post("/api/v1/terminal/execute", json={"command": "go notion"})
    assert go.status_code == 200
    body = go.json()
    assert body["action"] == "open_url"
    assert body["url"] == "https://notion.so"
