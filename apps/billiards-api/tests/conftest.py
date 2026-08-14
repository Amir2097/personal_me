"""Pytest fixtures for Цифровое Сукно API."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core import db
from app.core.db import get_session
from app.main import app
from app.services.auth_service import ensure_initial_admin


@pytest.fixture(name="client")
def client_fixture(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr("app.core.config.settings.auth_rate_limit_per_minute", 0)
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    db.engine = test_engine
    monkeypatch.setattr("app.core.db.create_db_and_tables", lambda: SQLModel.metadata.create_all(test_engine))

    with Session(test_engine) as session:
        ensure_initial_admin(session)

    def _get_session_override() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(client: TestClient, device_id: str = "test-device") -> dict[str, str]:
    response = client.post("/api/v1/billiards/auth/device", json={"device_id": device_id})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def register_user(client: TestClient, username: str, email: str, password: str = "Player123!"):
    return client.post(
        "/api/v1/billiards/auth/register",
        json={
            "username": username,
            "password": password,
            "email": email,
            "accept_terms": True,
        },
    )


def login_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def register_and_verify_player(client: TestClient, username: str, email: str, password: str = "Player123!"):
    reg = register_user(client, username, email, password=password)
    if reg.status_code != 200:
        return reg
    body = reg.json()
    token = body.get("verification_token")
    if body.get("verification_required") and token:
        verify_player(client, token)
    return reg


def verify_player(client: TestClient, token: str) -> None:
    response = client.post("/api/v1/billiards/auth/verify-email", json={"token": token})
    assert response.status_code == 200
