"""Academy progress on the dedicated API."""

from tests.conftest import auth_headers


def test_upsert_list_and_delete_progress(client):
    headers = auth_headers(client)
    saved = client.put(
        "/api/v1/academy/progress/ex_01_direct_target",
        headers=headers,
        json={"made": 7, "attempts": 10, "updated_at": "2026-08-10T12:00:00Z"},
    )
    assert saved.status_code == 200
    listed = client.get("/api/v1/academy/progress", headers=headers)
    assert any(item["exercise_id"] == "ex_01_direct_target" for item in listed.json()["items"])
    assert client.delete("/api/v1/academy/progress/ex_01_direct_target", headers=headers).status_code == 204
