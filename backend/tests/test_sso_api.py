"""SSO lite tests."""

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient


def test_go_service_appends_sso_code(client: TestClient):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login.json()["access_token"]

    go = client.post(
        "/api/v1/terminal/execute",
        json={"command": "go grafana"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert go.status_code == 200
    url = go.json()["url"]
    assert "sso_code=" in url

    query = parse_qs(urlparse(url).query)
    code = query["sso_code"][0]

    exchange = client.post("/api/v1/auth/sso/exchange", json={"code": code})
    assert exchange.status_code == 200
    body = exchange.json()
    assert body["username"] == "admin"
    assert body["access_token"]

    reuse = client.post("/api/v1/auth/sso/exchange", json={"code": code})
    assert reuse.status_code == 400
