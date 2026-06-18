"""Password reset via email tests."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_auth_config_reports_email_reset(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "smtp_host", "")
    response = client.get("/api/v1/auth/config")
    assert response.status_code == 200
    assert response.json()["password_reset_via_email"] is False

    monkeypatch.setattr(settings, "smtp_host", "mailpit")
    response = client.get("/api/v1/auth/config")
    assert response.json()["password_reset_via_email"] is True


def test_reset_sends_email_when_configured(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "smtp_host", "mailpit")
    monkeypatch.setattr(settings, "smtp_port", 1025)
    monkeypatch.setattr(settings, "smtp_use_tls", False)
    monkeypatch.setattr(settings, "expose_reset_token", False)
    monkeypatch.setattr(settings, "initial_admin_email", "admin@test.local")

    with patch("app.services.auth_service.send_password_reset_email") as send_mock:
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"username": "admin"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["reset_token"] is None
    send_mock.assert_called_once()
    args = send_mock.call_args[0]
    assert args[0] == "admin@test.local"
    assert "/reset-password?token=" in args[1]


def test_reset_by_email_login(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "smtp_host", "mailpit")
    monkeypatch.setattr(settings, "smtp_use_tls", False)
    monkeypatch.setattr(settings, "expose_reset_token", False)
    monkeypatch.setattr(settings, "initial_admin_email", "admin@test.local")

    with patch("app.services.auth_service.send_password_reset_email"):
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"username": "admin@test.local"},
        )
    assert response.status_code == 200


def test_reset_email_failure_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "smtp_host", "mailpit")
    monkeypatch.setattr(settings, "smtp_use_tls", False)
    monkeypatch.setattr(settings, "expose_reset_token", False)
    monkeypatch.setattr(settings, "initial_admin_email", "admin@test.local")

    with patch(
        "app.services.auth_service.send_password_reset_email",
        side_effect=RuntimeError("smtp down"),
    ):
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"username": "admin"},
        )
    assert response.status_code == 503
