"""Feedback form API tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def feedback_ready(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.core.config.settings.smtp_host", "mailpit")
    monkeypatch.setattr("app.core.config.settings.feedback_to_email", "owner@example.com")
    monkeypatch.setattr(
        "app.services.feedback_service.send_feedback_email",
        lambda **_: None,
    )


def test_feedback_config_disabled_by_default(client: TestClient):
    response = client.get("/api/v1/feedback/config")
    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_feedback_config_enabled(feedback_ready, client: TestClient):
    response = client.get("/api/v1/feedback/config")
    assert response.status_code == 200
    assert response.json()["enabled"] is True


def test_submit_feedback(feedback_ready, client: TestClient):
    response = client.post(
        "/api/v1/feedback",
        json={
            "name": "Guest",
            "email": "guest@example.com",
            "message": "Привет! Хочу обсудить проект.",
        },
    )
    assert response.status_code == 201
    assert "отправлено" in response.json()["message"].lower()


def test_submit_feedback_honeypot_silent(feedback_ready, client: TestClient, monkeypatch):
    called = {"value": False}

    def _fail(**_):
        called["value"] = True

    monkeypatch.setattr("app.services.feedback_service.send_feedback_email", _fail)
    response = client.post(
        "/api/v1/feedback",
        json={
            "name": "Bot",
            "email": "bot@example.com",
            "message": "Spam message here!!!",
            "company": "Evil Corp",
        },
    )
    assert response.status_code == 201
    assert called["value"] is False
