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


@pytest.fixture(name="client")
def client_fixture() -> Generator[TestClient, None, None]:
    """Create isolated test client with SQLite database."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    db.engine = test_engine
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as seed_session:
        ensure_initial_admin(seed_session)

    def _get_session_override() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
