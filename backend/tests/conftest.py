"""Pytest fixtures for API smoke tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core import db
from app.core.db import get_session
from app.main import app
from app.services.auth_service import ensure_initial_admin
from app.services.integration_service import ensure_default_integrations
from app.services.oidc_service import ensure_default_oauth_client
from app.services.project_service import ensure_default_projects


def _seed_test_database(engine) -> None:
    """Создать схему и сиды для изолированного SQLite."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as seed_session:
        ensure_initial_admin(seed_session)
        ensure_default_integrations(seed_session)
        ensure_default_projects(seed_session)
        ensure_default_oauth_client(seed_session)


@pytest.fixture(name="client")
def client_fixture(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    """Create isolated test client with SQLite database."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr("app.core.config.settings.allow_registration", True)
    monkeypatch.setattr("app.core.config.settings.expose_reset_token", True)
    monkeypatch.setattr("app.core.config.settings.initial_admin_email", "admin@test.local")
    db.engine = test_engine
    _seed_test_database(test_engine)

    def _initialize_database_override(*_args, **_kwargs) -> None:
        _seed_test_database(test_engine)

    monkeypatch.setattr("app.main.initialize_database", _initialize_database_override)

    def _get_session_override() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
