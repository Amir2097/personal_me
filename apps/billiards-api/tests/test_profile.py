"""User profile fields and avatar upload."""

from app.core.config import settings
from tests.conftest import login_headers, register_and_verify_player

MINI_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_patch_profile_updates_public_fields(client, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    register_and_verify_player(client, "profiler", "profiler@localhost")
    headers = login_headers(client, "profiler", "Player123!")

    patched = client.patch(
        "/api/v1/billiards/auth/profile",
        headers=headers,
        json={
            "display_name": "Иван Кий",
            "bio": "Играю в пирамиду",
            "location": "Казань",
            "telegram": "@ivan_cue",
        },
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["display_name"] == "Иван Кий"
    assert body["bio"] == "Играю в пирамиду"
    assert body["location"] == "Казань"
    assert body["telegram"] == "ivan_cue"

    me = client.get("/api/v1/billiards/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["display_name"] == "Иван Кий"


def test_upload_and_delete_avatar(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    register_and_verify_player(client, "avatar_user", "avatar_user@localhost")
    headers = login_headers(client, "avatar_user", "Player123!")

    upload = client.post(
        "/api/v1/billiards/auth/avatar",
        headers=headers,
        files={"file": ("avatar.png", MINI_PNG, "image/png")},
    )
    assert upload.status_code == 200
    body = upload.json()
    assert body["avatar_url"].startswith("/api/v1/billiards/uploads/avatars/")
    filename = body["avatar_url"].rsplit("/avatars/", 1)[-1]
    stored = tmp_path / "avatars" / filename
    assert stored.is_file()
    assert stored.read_bytes() == MINI_PNG

    me = client.get("/api/v1/billiards/auth/me", headers=headers)
    assert me.json()["avatar_url"] == body["avatar_url"]

    delete = client.delete("/api/v1/billiards/auth/avatar", headers=headers)
    assert delete.status_code == 200
    assert delete.json()["avatar_url"] == ""
    assert not stored.exists()


def test_device_cannot_update_profile(client):
    device = client.post("/api/v1/billiards/auth/device", json={"device_id": "profile-guest"})
    headers = {"Authorization": f"Bearer {device.json()['access_token']}"}
    denied = client.patch(
        "/api/v1/billiards/auth/profile",
        headers=headers,
        json={"display_name": "Гость"},
    )
    assert denied.status_code == 403
