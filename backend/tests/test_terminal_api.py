"""Smoke/e2e tests for auth and terminal command flow."""


def test_login_terminal_projects_and_logout_flow(client):
    """Verify login, projects list, refresh, and logout flow."""
    guest_projects = client.post("/api/v1/terminal/execute", json={"command": "projects"})
    assert guest_projects.status_code == 200
    assert guest_projects.json()["requires_auth"] is False
    assert "personal-me" in guest_projects.json()["output"]

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
    assert "infra-playground" in authorized.json()["output"]

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
        json={"username": "newuser", "password": "newuser123", "accept_terms": True},
    )
    assert register_response.status_code == 201
    created_tokens = register_response.json()
    assert created_tokens["access_token"]
    assert created_tokens["refresh_token"]

    duplicate_register = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "newuser123", "accept_terms": True},
    )
    assert duplicate_register.status_code == 409

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "newuser", "password": "newuser123"},
    )
    assert login_response.status_code == 200


def test_services_and_go_commands(client):
    """Проверка списка сервисов и перехода go."""
    services = client.post("/api/v1/terminal/execute", json={"command": "services"})
    assert services.status_code == 200
    body = services.json()
    assert body["requires_auth"] is False
    assert "github" in body["output"]
    assert "go <сервис>" in body["output"]

    go_public = client.post("/api/v1/terminal/execute", json={"command": "go github"})
    assert go_public.status_code == 200
    go_body = go_public.json()
    assert go_body["action"] == "open_url"
    assert go_body["url"] == "https://github.com"
    assert "GitHub" in go_body["output"]

    go_protected = client.post("/api/v1/terminal/execute", json={"command": "go grafana"})
    assert go_protected.status_code == 200
    assert go_protected.json()["requires_auth"] is True

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    tokens = login_response.json()

    go_auth = client.post(
        "/api/v1/terminal/execute",
        json={"command": "go grafana"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert go_auth.status_code == 200
    auth_body = go_auth.json()
    assert auth_body["requires_auth"] is False
    assert auth_body["action"] == "open_url"
    assert auth_body["url"].startswith("http://localhost:3001")
    assert "sso_code=" in auth_body["url"]

    go_unknown = client.post("/api/v1/terminal/execute", json={"command": "go unknown"})
    assert go_unknown.status_code == 200
    assert "не найден" in go_unknown.json()["output"]


def test_password_reset_and_change_flow(client):
    """Проверка сброса и смены пароля."""
    reset_request = client.post(
        "/api/v1/auth/password-reset/request",
        json={"username": "admin"},
    )
    assert reset_request.status_code == 200
    reset_data = reset_request.json()
    assert reset_data["reset_token"]

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_data["reset_token"], "new_password": "admin45678"},
    )
    assert confirm.status_code == 204

    old_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin45678"},
    )
    assert new_login.status_code == 200
    tokens = new_login.json()

    change = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "admin45678", "new_password": "admin12345"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert change.status_code == 204

    final_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin12345"},
    )
    assert final_login.status_code == 200
