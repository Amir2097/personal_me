"""Tests for academy progress API."""


def _login(client) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upsert_list_and_delete_progress(client):
    headers = _login(client)

    saved = client.put(
        "/api/v1/academy/progress/ex_01_direct_target",
        headers=headers,
        json={"made": 7, "attempts": 10, "updated_at": "2026-08-10T12:00:00Z"},
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["exercise_id"] == "ex_01_direct_target"
    assert body["made"] == 7
    assert body["attempts"] == 10

    listed = client.get("/api/v1/academy/progress", headers=headers)
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert any(item["exercise_id"] == "ex_01_direct_target" and item["made"] == 7 for item in items)

    deleted = client.delete("/api/v1/academy/progress/ex_01_direct_target", headers=headers)
    assert deleted.status_code == 204

    listed2 = client.get("/api/v1/academy/progress", headers=headers)
    assert listed2.status_code == 200
    assert all(item["exercise_id"] != "ex_01_direct_target" for item in listed2.json()["items"])


def test_bulk_merge_keeps_newer(client):
    headers = _login(client)

    client.put(
        "/api/v1/academy/progress/ex_03_stop_shot",
        headers=headers,
        json={"made": 8, "attempts": 10, "updated_at": "2026-08-10T15:00:00Z"},
    )

    merged = client.put(
        "/api/v1/academy/progress",
        headers=headers,
        json={
            "items": [
                {
                    "exercise_id": "ex_03_stop_shot",
                    "made": 3,
                    "attempts": 10,
                    "updated_at": "2026-08-10T10:00:00Z",
                },
                {
                    "exercise_id": "ex_07_bank_shot",
                    "made": 5,
                    "attempts": 8,
                    "updated_at": "2026-08-10T16:00:00Z",
                },
            ]
        },
    )
    assert merged.status_code == 200
    by_id = {item["exercise_id"]: item for item in merged.json()["items"]}
    assert by_id["ex_03_stop_shot"]["made"] == 8
    assert by_id["ex_07_bank_shot"]["made"] == 5


def test_academy_progress_requires_auth(client):
    assert client.get("/api/v1/academy/progress").status_code == 401
    assert client.put("/api/v1/academy/progress/ex_01", json={"made": 1, "attempts": 1}).status_code == 401
