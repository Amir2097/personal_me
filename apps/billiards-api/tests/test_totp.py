"""TOTP 2FA for admin/operator accounts."""

import pyotp
import pytest

from app.core.config import settings
from tests.conftest import login_headers, register_and_verify_player


@pytest.fixture(autouse=True)
def _disable_auth_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "auth_rate_limit_per_minute", 0)


def _enable_totp_for_user(client, headers: dict[str, str]) -> str:
    setup = client.post("/api/v1/billiards/auth/totp/setup", headers=headers)
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    code = pyotp.TOTP(secret).now()
    enabled = client.post(
        "/api/v1/billiards/auth/totp/enable",
        headers=headers,
        json={"code": code},
    )
    assert enabled.status_code == 200
    assert enabled.json()["enabled"] is True
    return secret


def test_player_cannot_setup_totp(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_and_verify_player(client, "totp_player", "totp_player@localhost")
    headers = login_headers(client, "totp_player", "Player123!")
    denied = client.post("/api/v1/billiards/auth/totp/setup", headers=headers)
    assert denied.status_code == 403


def test_operator_login_requires_totp(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_and_verify_player(client, "totp_op", "totp_op@localhost")
    admin_headers = login_headers(client, settings.initial_admin_username, settings.initial_admin_password)
    client.patch(
        "/api/v1/site/admin/users/totp_op",
        headers=admin_headers,
        json={"role": "operator"},
    )
    op_headers = login_headers(client, "totp_op", "Player123!")
    secret = _enable_totp_for_user(client, op_headers)

    login = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "totp_op", "password": "Player123!"},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["requires_totp"] is True
    assert body["challenge_token"]
    assert body["access_token"] is None

    code = pyotp.TOTP(secret).now()
    verified = client.post(
        "/api/v1/billiards/auth/totp/verify",
        json={"challenge_token": body["challenge_token"], "code": code},
    )
    assert verified.status_code == 200
    assert verified.json()["username"] == "totp_op"


def test_disable_totp(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    headers = login_headers(client, settings.initial_admin_username, settings.initial_admin_password)
    secret = _enable_totp_for_user(client, headers)

    code = pyotp.TOTP(secret).now()
    disabled = client.post(
        "/api/v1/billiards/auth/totp/disable",
        headers=headers,
        json={"password": settings.initial_admin_password, "code": code},
    )
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False

    login = client.post(
        "/api/v1/billiards/auth/login",
        json={
            "username": settings.initial_admin_username,
            "password": settings.initial_admin_password,
        },
    )
    assert login.status_code == 200
    assert login.json()["requires_totp"] is False
    assert login.json()["access_token"]
