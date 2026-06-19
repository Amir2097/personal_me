"""Site and terminal command tests."""

from fastapi.testclient import TestClient


def test_site_about_endpoint(client: TestClient):
    response = client.get("/api/v1/site/about")
    assert response.status_code == 200
    body = response.json()
    assert "owner_name" in body
    assert body["tagline"]
    assert isinstance(body["skills"], list)


def test_site_status_endpoint(client: TestClient):
    response = client.get("/api/v1/site/status")
    assert response.status_code == 200
    body = response.json()
    assert body["api"] == "ok"
    assert body["database"] == "ok"


def test_terminal_about_command(client: TestClient):
    response = client.post("/api/v1/terminal/execute", json={"command": "about"})
    assert response.status_code == 200
    output = response.json()["output"]
    assert "projects" in output
    assert "/about" in output


def test_terminal_status_command(client: TestClient):
    response = client.post("/api/v1/terminal/execute", json={"command": "status"})
    assert response.status_code == 200
    assert "database:" in response.json()["output"]


def test_terminal_man_command(client: TestClient):
    response = client.post("/api/v1/terminal/execute", json={"command": "man go"})
    assert response.status_code == 200
    assert "go <service>" in response.json()["output"]


def test_terminal_help_grouped(client: TestClient):
    response = client.post("/api/v1/terminal/execute", json={"command": "help"})
    assert response.status_code == 200
    output = response.json()["output"]
    assert "[portfolio]" in output
    assert "[services]" in output
    assert "[auth]" in output


def test_auth_profile_includes_email(client: TestClient):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert "email" in me.json()
