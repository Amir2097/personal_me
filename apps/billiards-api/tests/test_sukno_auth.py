"""Sukno account auth."""

from app.core.config import settings
from tests.conftest import auth_headers, login_headers, register_user


def test_auth_config(client):
    response = client.get("/api/v1/billiards/auth/config")
    assert response.status_code == 200
    body = response.json()
    assert "allow_registration" in body
    assert "require_email_verification" in body
    assert body["allow_legacy_admin_key"] is False


def test_register_requires_verification_before_login(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", True)
    monkeypatch.setattr(settings, "expose_verification_token", True)
    reg = register_user(client, "player1", "player1@localhost")
    assert reg.status_code == 200
    body = reg.json()
    assert body["verification_required"] is True
    assert body["verification_token"]

    denied = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "player1", "password": "Player123!"},
    )
    assert denied.status_code == 403

    verified = client.post(
        "/api/v1/billiards/auth/verify-email",
        json={"token": body["verification_token"]},
    )
    assert verified.status_code == 200
    assert verified.json()["email_verified"] is True

    login = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "player1", "password": "Player123!"},
    )
    assert login.status_code == 200
    assert login.json()["username"] == "player1"


def test_login_refresh_logout(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_user(client, "player2", "player2@localhost")
    login = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "player2", "password": "Player123!"},
    )
    assert login.status_code == 200
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = client.get("/api/v1/billiards/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["source"] == "account"

    refreshed = client.post(
        "/api/v1/billiards/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200

    logout = client.post(
        "/api/v1/billiards/auth/logout",
        json={"refresh_token": refreshed.json()["refresh_token"]},
    )
    assert logout.status_code == 200


def test_admin_account_can_manage_users(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    admin_headers = login_headers(client, settings.initial_admin_username, settings.initial_admin_password)
    users = client.get("/api/v1/site/admin/users", headers=admin_headers)
    assert users.status_code == 200
    assert any(item["username"] == settings.initial_admin_username for item in users.json())

    reg = register_user(client, "operator1", "operator1@localhost")
    assert reg.status_code == 200
    if reg.json().get("verification_required"):
        client.post(
            "/api/v1/billiards/auth/verify-email",
            json={"token": reg.json()["verification_token"]},
        )

    patched = client.patch(
        "/api/v1/site/admin/users/operator1",
        headers=admin_headers,
        json={"role": "operator", "display_name": "Оператор зала"},
    )
    assert patched.status_code == 200
    assert patched.json()["role"] == "operator"
    assert patched.json()["display_name"] == "Оператор зала"


def test_device_still_works(client):
    headers = auth_headers(client)
    me = client.get("/api/v1/billiards/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["source"] == "device"
