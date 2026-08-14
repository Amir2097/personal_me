"""Site SEO and admin unlock."""

from app.core.config import settings
from tests.conftest import auth_headers


def test_public_seo_is_open(client):
    response = client.get("/api/v1/site/seo")
    assert response.status_code == 200
    body = response.json()
    assert body["brand_name"] == "Цифровое Сукно"
    assert "бильярд" in body["seo_description"].lower() or body["seo_title"]


def test_settings_require_admin(client):
    assert client.get("/api/v1/site/settings").status_code == 401
    device = auth_headers(client)
    assert client.get("/api/v1/site/settings", headers=device).status_code == 403


def test_unlock_and_update_seo(client, monkeypatch):
    monkeypatch.setattr(settings, "allow_legacy_admin_key", True)
    monkeypatch.setattr(settings, "sukno_admin_key", "test-admin-key")
    denied = client.post("/api/v1/site/admin/unlock", json={"key": "wrong"})
    assert denied.status_code == 401

    unlocked = client.post("/api/v1/site/admin/unlock", json={"key": "test-admin-key"})
    assert unlocked.status_code == 200
    headers = {"Authorization": f"Bearer {unlocked.json()['access_token']}"}

    patched = client.patch(
        "/api/v1/site/settings",
        headers=headers,
        json={
            "tagline": "Сукно для зала",
            "seo_title": "Цифровое Сукно · зал",
            "seo_description": "Турниры и колхоз.",
            "site_url": "https://sukno.example",
        },
    )
    assert patched.status_code == 200
    assert patched.json()["brand_name"] == "Цифровое Сукно"
    assert patched.json()["tagline"] == "Сукно для зала"

    public = client.get("/api/v1/site/seo")
    assert public.json()["seo_title"] == "Цифровое Сукно · зал"
    assert public.json()["site_url"] == "https://sukno.example"


def test_legacy_unlock_disabled_by_default(client, monkeypatch):
    monkeypatch.setattr(settings, "sukno_admin_key", "test-admin-key")
    monkeypatch.setattr(settings, "allow_legacy_admin_key", False)
    response = client.post("/api/v1/site/admin/unlock", json={"key": "test-admin-key"})
    assert response.status_code == 403
    assert "отключён" in response.json()["detail"].lower()


def test_legacy_admin_jwt_rejected_when_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "allow_legacy_admin_key", True)
    monkeypatch.setattr(settings, "sukno_admin_key", "test-admin-key")
    unlocked = client.post("/api/v1/site/admin/unlock", json={"key": "test-admin-key"})
    token = unlocked.json()["access_token"]
    monkeypatch.setattr(settings, "allow_legacy_admin_key", False)
    assert client.get("/api/v1/site/settings", headers={"Authorization": f"Bearer {token}"}).status_code == 403
