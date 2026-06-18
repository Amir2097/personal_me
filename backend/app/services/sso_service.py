"""SSO one-time code service."""

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import create_access_token
from app.models.sso_code import SsoCode


def create_sso_code(session: Session, username: str, service_key: str) -> str:
    """Создать одноразовый SSO-код."""
    code = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.sso_code_expire_seconds
    )
    session.add(
        SsoCode(
            code=code,
            username=username,
            service_key=service_key,
            expires_at=expires_at,
            used=False,
        )
    )
    session.commit()
    return code


def append_sso_code_to_url(base_url: str, code: str) -> str:
    """Добавить sso_code к URL сервиса."""
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query))
    query["sso_code"] = code
    return urlunparse(parsed._replace(query=urlencode(query)))


def exchange_sso_code(session: Session, code: str) -> tuple[str, str]:
    """Обменять код на access token для целевого сервиса."""
    stored = session.exec(select(SsoCode).where(SsoCode.code == code)).first()
    if (
        not stored
        or stored.used
        or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSO-код недействителен или истёк.",
        )

    stored.used = True
    session.add(stored)
    session.commit()
    access_token = create_access_token(stored.username)
    return stored.username, access_token
