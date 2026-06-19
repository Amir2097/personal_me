"""Contact channels API tests."""

from fastapi.testclient import TestClient


def _admin_client(client: TestClient) -> TestClient:
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    return client


def test_contacts_public_list(client: TestClient):
    response = client.get("/api/v1/contacts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_contact_terminal_command(client: TestClient):
    client = _admin_client(client)
    create = client.post(
        "/api/v1/contacts",
        json={
            "key": "telegram",
            "label": "Telegram",
            "value": "https://t.me/amir",
            "kind": "link",
        },
    )
    assert create.status_code == 201

    response = client.post("/api/v1/terminal/execute", json={"command": "contact"})
    assert response.status_code == 200
    output = response.json()["output"]
    assert "telegram" in output
    assert "/contact" in output

    open_contact = client.post(
        "/api/v1/terminal/execute",
        json={"command": "contact telegram"},
    )
    assert open_contact.status_code == 200
    body = open_contact.json()
    assert body["action"] == "open_url"
    assert body["url"] == "https://t.me/amir"


def test_contact_admin_crud(client: TestClient):
    client = _admin_client(client)
    created = client.post(
        "/api/v1/contacts",
        json={
            "key": "linkedin",
            "label": "LinkedIn",
            "value": "https://linkedin.com/in/amir",
            "kind": "link",
        },
    )
    assert created.status_code == 201
    item_id = created.json()["id"]
    assert created.json()["href"] == "https://linkedin.com/in/amir"

    updated = client.patch(
        f"/api/v1/contacts/{item_id}",
        json={"enabled": False},
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False

    public = client.get("/api/v1/contacts")
    assert all(item["id"] != item_id for item in public.json())

    deleted = client.delete(f"/api/v1/contacts/{item_id}")
    assert deleted.status_code == 204
