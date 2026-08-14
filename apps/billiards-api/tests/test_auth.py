"""Device identity for Цифровое Сукно."""

from tests.conftest import auth_headers


def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "sukno"


def test_device_session_is_stable(client):
    first = client.post("/api/v1/billiards/auth/device", json={"device_id": "abc-123"})
    second = client.post("/api/v1/billiards/auth/device", json={"device_id": "abc-123"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["username"] == second.json()["username"]
    assert first.json()["username"].startswith("local_")


def test_me_requires_token(client):
    assert client.get("/api/v1/billiards/auth/me").status_code == 401
    headers = auth_headers(client)
    me = client.get("/api/v1/billiards/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["source"] == "device"
