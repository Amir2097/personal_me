"""Site settings and SEO API tests."""

from fastapi.testclient import TestClient


def _admin(client: TestClient) -> TestClient:
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    return client


def test_site_seo_public(client: TestClient):
    response = client.get("/api/v1/site/seo")
    assert response.status_code == 200
    body = response.json()
    assert "site_name" in body
    assert "seo_description" in body


def test_site_settings_admin_update(client: TestClient):
    client = _admin(client)
    current = client.get("/api/v1/site/settings")
    assert current.status_code == 200

    updated = client.patch(
        "/api/v1/site/settings",
        json={
            "owner_name": "Amir",
            "tagline": "Developer hub test",
            "seo_keywords": "python, nuxt, terminal",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["owner_name"] == "Amir"
    assert body["tagline"] == "Developer hub test"

    seo = client.get("/api/v1/site/seo")
    assert seo.json()["owner_name"] == "Amir"

    about = client.get("/api/v1/site/about")
    assert about.json()["owner_name"] == "Amir"


def test_site_settings_requires_admin(client: TestClient):
    assert client.get("/api/v1/site/settings").status_code == 401
