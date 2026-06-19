"""Site legal documents API tests."""

from fastapi.testclient import TestClient


def test_site_legal_public(client: TestClient):
    response = client.get("/api/v1/site/legal")
    assert response.status_code == 200
    body = response.json()
    assert "privacy_policy" in body
    assert "terms_of_use" in body
    assert len(body["privacy_policy"]) > 100
    assert "152-ФЗ" in body["privacy_policy"] or "персональных данных" in body["privacy_policy"]


def test_register_requires_terms_acceptance(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "noterms",
            "password": "secret123",
            "accept_terms": False,
        },
    )
    assert response.status_code == 400
