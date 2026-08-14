"""HttpOnly cookie auth for Sukno accounts and device sessions."""

from app.core.config import settings
from app.core.cookies import SUKNO_ACCESS_COOKIE, SUKNO_REFRESH_COOKIE
from tests.conftest import login_headers, register_and_verify_player


def test_login_sets_httponly_cookies(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_and_verify_player(client, "cookie_user", "cookie_user@localhost")
    login = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "cookie_user", "password": "Player123!"},
    )
    assert login.status_code == 200
    assert SUKNO_ACCESS_COOKIE in login.cookies
    assert SUKNO_REFRESH_COOKIE in login.cookies

    me = client.get("/api/v1/billiards/auth/me")
    assert me.status_code == 200
    assert me.json()["source"] == "account"


def test_refresh_via_cookie(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_and_verify_player(client, "cookie_refresh", "cookie_refresh@localhost")
    login = client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "cookie_refresh", "password": "Player123!"},
    )
    assert login.status_code == 200

    refreshed = client.post("/api/v1/billiards/auth/refresh", json={})
    assert refreshed.status_code == 200
    assert refreshed.json()["username"] == "cookie_refresh"


def test_logout_clears_cookies(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_and_verify_player(client, "cookie_logout", "cookie_logout@localhost")
    client.post(
        "/api/v1/billiards/auth/login",
        json={"username": "cookie_logout", "password": "Player123!"},
    )
    logout = client.post("/api/v1/billiards/auth/logout", json={})
    assert logout.status_code == 200

    me = client.get("/api/v1/billiards/auth/me")
    assert me.status_code == 401


def test_device_sets_access_cookie(client):
    created = client.post("/api/v1/billiards/auth/device", json={"device_id": "cookie-device"})
    assert created.status_code == 200
    assert SUKNO_ACCESS_COOKIE in created.cookies
    assert SUKNO_REFRESH_COOKIE not in created.cookies

    me = client.get("/api/v1/billiards/auth/me")
    assert me.status_code == 200
    assert me.json()["source"] == "device"
