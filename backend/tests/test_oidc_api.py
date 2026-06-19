"""OIDC provider tests."""

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient


def test_oidc_discovery_and_jwks(client: TestClient):
    discovery = client.get("/api/v1/oidc/.well-known/openid-configuration")
    assert discovery.status_code == 200
    body = discovery.json()
    assert body["issuer"] == "http://localhost/api/v1/oidc"
    assert "authorization_endpoint" in body

    jwks = client.get("/api/v1/oidc/jwks")
    assert jwks.status_code == 200
    assert jwks.json()["keys"]


def test_oidc_authorization_code_flow(client: TestClient):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200

    approve = client.post(
        "/api/v1/oidc/authorize/approve",
        json={
            "client_id": "personal-me-dev",
            "redirect_uri": "http://localhost/oauth/callback",
            "scope": "openid profile",
            "state": "xyz",
            "nonce": "abc",
        },
    )
    assert approve.status_code == 200
    redirect_to = approve.json()["redirect_to"]
    query = parse_qs(urlparse(redirect_to).query)
    code = query["code"][0]
    assert query["state"][0] == "xyz"

    token = client.post(
        "/api/v1/oidc/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost/oauth/callback",
            "client_id": "personal-me-dev",
            "client_secret": "dev-secret-change-me",
        },
    )
    assert token.status_code == 200
    tokens = token.json()
    assert tokens["access_token"]
    assert tokens["id_token"]

    userinfo = client.get(
        "/api/v1/oidc/userinfo",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert userinfo.status_code == 200
    assert userinfo.json()["sub"] == "admin"


def test_oidc_pkce_authorization_code_flow(client: TestClient):
    import base64
    import hashlib
    import secrets

    code_verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200

    approve = client.post(
        "/api/v1/oidc/authorize/approve",
        json={
            "client_id": "personal-me-dev",
            "redirect_uri": "http://localhost/oauth/callback",
            "scope": "openid profile",
            "state": "pkce-state",
            "nonce": "pkce-nonce",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        },
    )
    assert approve.status_code == 200
    redirect_to = approve.json()["redirect_to"]
    code = parse_qs(urlparse(redirect_to).query)["code"][0]

    token = client.post(
        "/api/v1/oidc/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost/oauth/callback",
            "client_id": "personal-me-dev",
            "client_secret": "dev-secret-change-me",
            "code_verifier": code_verifier,
        },
    )
    assert token.status_code == 200
    assert token.json()["access_token"]
