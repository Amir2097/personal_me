"""Smoke/e2e tests for auth and terminal command flow."""


def test_login_terminal_projects_and_logout_flow(client):
    """Verify login, protected command, refresh, and logout flow."""
    unauthorized = client.post("/api/v1/terminal/execute", json={"command": "projects"})
    assert unauthorized.status_code == 200
    assert unauthorized.json()["requires_auth"] is True

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    authorized = client.post(
        "/api/v1/terminal/execute",
        json={"command": "projects"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert authorized.status_code == 200
    assert authorized.json()["requires_auth"] is False
    assert "Projects:" in authorized.json()["output"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["access_token"] != tokens["access_token"]
    assert refreshed["refresh_token"] != tokens["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed["refresh_token"]},
    )
    assert logout_response.status_code == 204

    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refreshed["refresh_token"]},
    )
    assert refresh_after_logout.status_code == 401


def test_register_and_login_flow(client):
    """Verify user registration and subsequent login."""
    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "newuser123"},
    )
    assert register_response.status_code == 201
    created_tokens = register_response.json()
    assert created_tokens["access_token"]
    assert created_tokens["refresh_token"]

    duplicate_register = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "newuser123"},
    )
    assert duplicate_register.status_code == 409

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "newuser", "password": "newuser123"},
    )
    assert login_response.status_code == 200
