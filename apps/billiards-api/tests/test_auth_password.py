"""Password reset and change-password flows."""

from app.core.config import settings
from tests.conftest import login_headers, register_user


def test_password_reset_flow(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    monkeypatch.setattr(settings, "expose_reset_token", True)
    register_user(client, "reset_user", "reset_user@localhost")

    req = client.post(
        "/api/v1/billiards/auth/password-reset/request",
        json={"login": "reset_user"},
    )
    assert req.status_code == 200
    token = req.json()["reset_token"]
    assert token

    confirm = client.post(
        "/api/v1/billiards/auth/password-reset/confirm",
        json={"token": token, "new_password": "NewPass456!"},
    )
    assert confirm.status_code == 200

    old_login = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "reset_user", "password": "Player123!"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "reset_user", "password": "NewPass456!"},
    )
    assert new_login.status_code == 200


def test_password_reset_unknown_login_is_generic(client):
    response = client.post(
        "/api/v1/billiards/auth/password-reset/request",
        json={"login": "nobody@localhost"},
    )
    assert response.status_code == 200
    assert response.json()["reset_token"] is None


def test_change_password(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_user(client, "pwd_user", "pwd_user@localhost")
    headers = login_headers(client, "pwd_user", "Player123!")

    bad = client.post(
        "/api/v1/billiards/auth/change-password",
        headers=headers,
        json={"current_password": "wrong", "new_password": "Another456!"},
    )
    assert bad.status_code == 401

    ok = client.post(
        "/api/v1/billiards/auth/change-password",
        headers=headers,
        json={"current_password": "Player123!", "new_password": "Another456!"},
    )
    assert ok.status_code == 200

    assert (
        client.post(
            "/api/v1/billiards/auth/login",
            json={"username": "pwd_user", "password": "Player123!"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/billiards/auth/login",
            json={"username": "pwd_user", "password": "Another456!"},
        ).status_code
        == 200
    )
