"""OIDC / OAuth2 authorization code flow."""

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException, status
from jose import jwt
from sqlmodel import Session, select

from app.core.config import settings
from app.core.oidc_keys import get_oidc_private_key_pem, get_oidc_public_jwks
from app.core.security import get_password_hash, verify_password
from app.models.oauth_authorization_code import OAuthAuthorizationCode
from app.models.oauth_client import OAuthClient
from app.models.user import User
from app.schemas.oidc import OAuthClientCreate, OidcTokenResponse, UserInfoResponse

DEFAULT_OAUTH_CLIENT = {
    "client_id": "personal-me-dev",
    "client_secret": "dev-secret-change-me",
    "name": "Personal Me Dev",
    "redirect_uris": [
        "http://localhost/oauth/callback",
        "http://127.0.0.1/oauth/callback",
    ],
    "scopes": "openid profile",
}


def _redirect_uris_list(raw: str) -> list[str]:
    if not raw.strip():
        return []
    if raw.strip().startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
    return [item.strip() for item in raw.split(",") if item.strip()]


def _redirect_uris_to_str(uris: list[str]) -> str:
    return json.dumps(uris)


def ensure_default_oauth_client(session: Session) -> None:
    """Сид dev OAuth клиента."""
    existing = session.exec(
        select(OAuthClient).where(OAuthClient.client_id == DEFAULT_OAUTH_CLIENT["client_id"])
    ).first()
    if existing:
        return
    session.add(
        OAuthClient(
            client_id=DEFAULT_OAUTH_CLIENT["client_id"],
            client_secret_hash=get_password_hash(DEFAULT_OAUTH_CLIENT["client_secret"]),
            name=DEFAULT_OAUTH_CLIENT["name"],
            redirect_uris=_redirect_uris_to_str(DEFAULT_OAUTH_CLIENT["redirect_uris"]),
            scopes=DEFAULT_OAUTH_CLIENT["scopes"],
            enabled=True,
        )
    )
    session.commit()


def list_oauth_clients(session: Session) -> list[OAuthClient]:
    return list(session.exec(select(OAuthClient).order_by(OAuthClient.client_id)).all())


def create_oauth_client(session: Session, payload: OAuthClientCreate) -> OAuthClient:
    existing = session.exec(
        select(OAuthClient).where(OAuthClient.client_id == payload.client_id)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="client_id уже занят.")
    item = OAuthClient(
        client_id=payload.client_id.strip(),
        client_secret_hash=get_password_hash(payload.client_secret),
        name=payload.name.strip() or payload.client_id,
        redirect_uris=_redirect_uris_to_str(payload.redirect_uris),
        scopes=payload.scopes.strip() or "openid profile",
        enabled=True,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_oauth_client(session: Session, client_id: int) -> None:
    item = session.get(OAuthClient, client_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден.")
    session.delete(item)
    session.commit()


def _get_client(session: Session, client_id: str) -> OAuthClient:
    client = session.exec(
        select(OAuthClient).where(OAuthClient.client_id == client_id)
    ).first()
    if not client or not client.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестный client_id.")
    return client


def _validate_redirect_uri(client: OAuthClient, redirect_uri: str) -> None:
    allowed = _redirect_uris_list(client.redirect_uris)
    if redirect_uri not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="redirect_uri не разрешён для клиента.",
        )


def _verify_pkce(code: OAuthAuthorizationCode, code_verifier: str | None) -> None:
    if not code.code_challenge:
        return
    if not code_verifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Требуется code_verifier.")
    method = code.code_challenge_method.upper() if code.code_challenge_method else "S256"
    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    else:
        challenge = code_verifier
    if challenge != code.code_challenge:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный code_verifier.")


def build_discovery_document() -> dict[str, Any]:
    """OpenID Provider Configuration."""
    issuer = settings.oidc_issuer.rstrip("/")
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/authorize",
        "token_endpoint": f"{issuer}/token",
        "userinfo_endpoint": f"{issuer}/userinfo",
        "jwks_uri": f"{issuer}/jwks",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256", "plain"],
    }


def build_authorize_redirect_url(
    session: Session,
    *,
    username: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    nonce: str,
    code_challenge: str,
    code_challenge_method: str,
) -> str:
    """Создать authorization code и вернуть redirect URL."""
    client = _get_client(session, client_id)
    _validate_redirect_uri(client, redirect_uri)

    code = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    session.add(
        OAuthAuthorizationCode(
            code=code,
            client_id=client.client_id,
            username=username,
            redirect_uri=redirect_uri,
            scope=scope or client.scopes,
            nonce=nonce,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            expires_at=expires_at,
            used=False,
        )
    )
    session.commit()

    parsed = urlparse(redirect_uri)
    query = dict(parse_qsl(parsed.query))
    query["code"] = code
    if state:
        query["state"] = state
    return urlunparse(parsed._replace(query=urlencode(query)))


def authenticate_client(
    session: Session,
    client_id: str | None,
    client_secret: str | None,
) -> OAuthClient:
    """Проверить client_id + client_secret."""
    if not client_id or not client_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные client credentials.")
    client = _get_client(session, client_id)
    if not verify_password(client_secret, client.client_secret_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные client credentials.")
    return client


def exchange_authorization_code(
    session: Session,
    *,
    client: OAuthClient,
    code: str,
    redirect_uri: str,
    code_verifier: str | None,
) -> OidcTokenResponse:
    """Обменять authorization code на OIDC tokens."""
    stored = session.exec(
        select(OAuthAuthorizationCode).where(OAuthAuthorizationCode.code == code)
    ).first()
    if (
        not stored
        or stored.used
        or stored.client_id != client.client_id
        or stored.redirect_uri != redirect_uri
        or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недействительный code.")

    _verify_pkce(stored, code_verifier)

    user = session.exec(select(User).where(User.username == stored.username)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь не найден.")

    stored.used = True
    session.add(stored)
    session.commit()

    return _issue_oidc_tokens(user, stored.scope, stored.nonce, client.client_id)


def _issue_oidc_tokens(
    user: User,
    scope: str,
    nonce: str,
    audience: str,
) -> OidcTokenResponse:
    """Выдать RS256 access_token и id_token."""
    now = datetime.now(timezone.utc)
    expires_in = settings.access_token_expire_minutes * 60
    issuer = settings.oidc_issuer.rstrip("/")
    private_key = get_oidc_private_key_pem()

    access_payload = {
        "iss": issuer,
        "sub": user.username,
        "aud": audience,
        "exp": now + timedelta(seconds=expires_in),
        "iat": now,
        "scope": scope,
    }
    access_token = jwt.encode(access_payload, private_key, algorithm="RS256")

    id_payload = {
        "iss": issuer,
        "sub": user.username,
        "aud": audience,
        "exp": now + timedelta(seconds=expires_in),
        "iat": now,
        "preferred_username": user.username,
        "is_admin": user.is_admin,
    }
    if nonce:
        id_payload["nonce"] = nonce
    id_token = jwt.encode(id_payload, private_key, algorithm="RS256")

    return OidcTokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        id_token=id_token,
        scope=scope,
    )


def decode_oidc_access_token(token: str) -> dict[str, Any]:
    """Декодировать OIDC access token (RS256)."""
    private_key = serialization.load_pem_private_key(
        get_oidc_private_key_pem().encode("utf-8"),
        password=None,
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return jwt.decode(
        token,
        public_pem,
        algorithms=["RS256"],
        issuer=settings.oidc_issuer.rstrip("/"),
        options={"verify_aud": False},
    )


def get_userinfo(session: Session, access_token: str) -> UserInfoResponse:
    """OIDC UserInfo endpoint."""
    payload = decode_oidc_access_token(access_token)
    username = payload.get("sub")
    if not isinstance(username, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserInfoResponse(
        sub=user.username,
        preferred_username=user.username,
        is_admin=user.is_admin,
    )
