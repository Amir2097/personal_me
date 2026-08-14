"""Admin audit log."""

from app.core.config import settings
from tests.conftest import login_headers, register_and_verify_player


def test_user_update_is_audited(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_and_verify_player(client, "audit_target", "audit_target@localhost")
    admin_headers = login_headers(client, settings.initial_admin_username, settings.initial_admin_password)

    patched = client.patch(
        "/api/v1/site/admin/users/audit_target",
        headers=admin_headers,
        json={"role": "operator"},
    )
    assert patched.status_code == 200

    audit = client.get("/api/v1/site/admin/audit", headers=admin_headers)
    assert audit.status_code == 200
    entries = audit.json()
    assert any(
        item["action"] == "admin.user.update"
        and item["target"] == "audit_target"
        and item["details"].get("role", {}).get("to") == "operator"
        for item in entries
    )


def test_site_settings_update_is_audited(client, monkeypatch):
    monkeypatch.setattr(settings, "allow_legacy_admin_key", True)
    monkeypatch.setattr(settings, "sukno_admin_key", "test-admin-key")
    unlocked = client.post("/api/v1/site/admin/unlock", json={"key": "test-admin-key"})
    headers = {"Authorization": f"Bearer {unlocked.json()['access_token']}"}

    patched = client.patch(
        "/api/v1/site/settings",
        headers=headers,
        json={"tagline": "Audit test tagline"},
    )
    assert patched.status_code == 200

    audit = client.get("/api/v1/site/admin/audit", headers=headers)
    assert audit.status_code == 200
    assert any(
        item["action"] == "site.settings.update" and "tagline" in item["details"]
        for item in audit.json()
    )


def test_legacy_unlock_is_audited(client, monkeypatch):
    monkeypatch.setattr(settings, "allow_legacy_admin_key", True)
    monkeypatch.setattr(settings, "sukno_admin_key", "audit-key")
    client.post("/api/v1/site/admin/unlock", json={"key": "audit-key"})
    admin_headers = login_headers(client, settings.initial_admin_username, settings.initial_admin_password)

    audit = client.get("/api/v1/site/admin/audit", headers=admin_headers)
    assert audit.status_code == 200
    assert any(item["action"] == "admin.legacy_unlock" for item in audit.json())
