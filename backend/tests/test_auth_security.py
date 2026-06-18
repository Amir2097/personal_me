"""Security-related auth tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_login_sets_auth_cookies(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    assert response.cookies.get("access_token")
    assert response.cookies.get("refresh_token")


def test_registration_disabled(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "allow_registration", False)
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "blocked_user", "password": "blocked123"},
    )
    assert response.status_code == 403


def test_reset_token_hidden_when_disabled(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "expose_reset_token", False)
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"username": "admin"},
    )
    assert response.status_code == 200
    assert response.json()["reset_token"] is None


def test_auth_config_endpoint(client: TestClient):
    response = client.get("/api/v1/auth/config")
    assert response.status_code == 200
    body = response.json()
    assert "allow_registration" in body
    assert "expose_reset_token" in body
    assert "password_reset_via_email" in body
