"""Tests for portfolio projects API."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_public_projects(client: TestClient):
    """Гость видит только публичные проекты."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()}
    assert "personal-me" in slugs
    assert "infra-playground" not in slugs


def test_private_project_visible_when_authenticated(client: TestClient, admin_headers: dict):
    """Авторизованный пользователь видит приватные проекты."""
    response = client.get("/api/v1/projects", headers=admin_headers)
    slugs = {item["slug"] for item in response.json()}
    assert "infra-playground" in slugs


def test_get_project_by_slug(client: TestClient):
    response = client.get("/api/v1/projects/personal-me")
    assert response.status_code == 200
    assert response.json()["title"] == "Personal Me"


def test_private_slug_hidden_from_guest(client: TestClient):
    response = client.get("/api/v1/projects/infra-playground")
    assert response.status_code == 404


def test_projects_admin_crud(client: TestClient, admin_headers: dict[str, str]):
    create = client.post(
        "/api/v1/projects",
        json={
            "slug": "new-app",
            "title": "New App",
            "summary": "Test project",
            "is_public": True,
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    created = create.json()
    project_id = created["id"]

    patch = client.patch(
        f"/api/v1/projects/{project_id}",
        json={
            "summary": "Updated summary",
            "image_url": "https://example.com/cover.png",
            "gallery_urls": "https://example.com/a.png\nhttps://example.com/b.png",
        },
        headers=admin_headers,
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["summary"] == "Updated summary"
    assert body["image_url"] == "https://example.com/cover.png"
    assert body["gallery"] == [
        "https://example.com/a.png",
        "https://example.com/b.png",
    ]

    delete = client.delete(f"/api/v1/projects/{project_id}", headers=admin_headers)
    assert delete.status_code == 204


def test_terminal_projects_commands(client: TestClient):
    """Terminal-команды projects и project."""
    projects = client.post("/api/v1/terminal/execute", json={"command": "projects"})
    assert projects.status_code == 200
    assert "personal-me" in projects.json()["output"]
    assert "infra-playground" not in projects.json()["output"]

    detail = client.post(
        "/api/v1/terminal/execute",
        json={"command": "project personal-me"},
    )
    assert detail.status_code == 200
    assert "Personal Me" in detail.json()["output"]
