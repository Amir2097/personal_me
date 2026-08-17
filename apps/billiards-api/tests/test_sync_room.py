"""Sync room security: code length and TTL."""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core import db
from app.core.config import settings
from app.models.kolkhoz_session import KolkhozSession
from tests.conftest import operator_headers


def test_room_code_length(client):
    headers = operator_headers(client)
    created = client.post("/api/v1/kolkhoz/sessions", headers=headers)
    assert created.status_code == 200
    code = created.json()["code"]
    assert len(code) == settings.sync_room_code_length
    assert len(code) >= 8


def test_expired_kolkhoz_room_returns_404(client):
    headers = operator_headers(client)
    created = client.post("/api/v1/kolkhoz/sessions", headers=headers)
    code = created.json()["code"]

    with Session(db.engine) as session:
        row = session.exec(select(KolkhozSession).where(KolkhozSession.code == code)).first()
        assert row is not None
        row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        session.add(row)
        session.commit()

    assert client.get(f"/api/v1/kolkhoz/sessions/{code}").status_code == 404


def test_push_extends_room_ttl(client):
    headers = operator_headers(client)
    created = client.post("/api/v1/kolkhoz/sessions", headers=headers)
    code = created.json()["code"]

    with Session(db.engine) as session:
        row = session.exec(select(KolkhozSession).where(KolkhozSession.code == code)).first()
        assert row is not None
        row.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        session.add(row)
        session.commit()

    pushed = client.put(
        f"/api/v1/kolkhoz/sessions/{code}",
        headers=headers,
        json={"state": {"version": 1, "mode": "casual", "players": [], "events": []}},
    )
    assert pushed.status_code == 200

    with Session(db.engine) as session:
        row = session.exec(select(KolkhozSession).where(KolkhozSession.code == code)).first()
        assert row is not None
        assert row.expires_at is not None
        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        assert expires > datetime.now(timezone.utc) + timedelta(hours=1)
