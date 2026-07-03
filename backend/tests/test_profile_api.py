"""User profile API tests."""

from fastapi.testclient import TestClient


def _login(client: TestClient, username: str = "admin", password: str = "admin123") -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200


def test_me_includes_profile_fields(client: TestClient):
    _login(client)
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "admin"
    assert "display_name" in body
    assert "avatar_url" in body
    assert "bio" in body
    assert "location" in body
    assert "website" in body
    assert "telegram" in body
    assert "github" in body


def test_patch_profile_updates_fields(client: TestClient):
    _login(client)
    patch = client.patch(
        "/api/v1/auth/profile",
        json={
            "display_name": "Nik Admin",
            "avatar_url": "https://example.com/avatar.png",
            "bio": "Backend dev",
            "location": "Moscow",
            "website": "https://dautovtech.dev",
            "telegram": "@nik",
            "github": "nikol",
            "email": "admin@example.com",
        },
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["display_name"] == "Nik Admin"
    assert body["avatar_url"] == "https://example.com/avatar.png"
    assert body["bio"] == "Backend dev"
    assert body["email"] == "admin@example.com"

    me = client.get("/api/v1/auth/me")
    assert me.json()["display_name"] == "Nik Admin"


MINI_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_upload_and_delete_avatar(client: TestClient, tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.uploads_dir", str(tmp_path))
    _login(client)

    upload = client.post(
        "/api/v1/auth/avatar",
        files={"file": ("avatar.png", MINI_PNG, "image/png")},
    )
    assert upload.status_code == 200
    body = upload.json()
    assert body["avatar_url"].startswith("/api/v1/uploads/avatars/")
    filename = body["avatar_url"].rsplit("/avatars/", 1)[-1]
    stored = tmp_path / "avatars" / filename
    assert stored.is_file()
    assert stored.read_bytes() == MINI_PNG

    delete = client.delete("/api/v1/auth/avatar")
    assert delete.status_code == 200
    assert delete.json()["avatar_url"] == ""


def test_patch_profile_allows_localhost_email(client: TestClient):
    _login(client)
    patch = client.patch(
        "/api/v1/auth/profile",
        json={
            "email": "admin@localhost",
            "avatar_url": "/api/v1/uploads/avatars/1_test.png",
        },
    )
    assert patch.status_code == 200
    assert patch.json()["email"] == "admin@localhost"


def test_change_password_requires_confirm_match(client: TestClient):
    _login(client)
    mismatch = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "admin123",
            "new_password": "newpass123",
            "new_password_confirm": "otherpass123",
        },
    )
    assert mismatch.status_code == 422

    ok = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "admin123",
            "new_password": "admin99999",
            "new_password_confirm": "admin99999",
        },
    )
    assert ok.status_code == 204

    old_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin99999"},
    )
    assert new_login.status_code == 200

    # restore password for other tests
    client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "admin99999",
            "new_password": "admin123",
            "new_password_confirm": "admin123",
        },
        headers={"Authorization": f"Bearer {new_login.json()['access_token']}"},
    )
