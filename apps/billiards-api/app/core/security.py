"""JWT and password helper utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str, *, token_type: str = "access") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "typ": token_type,
        "jti": uuid4().hex,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    jti = uuid4().hex
    payload: dict[str, Any] = {"sub": subject, "typ": "refresh", "jti": jti, "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def is_refresh_payload(payload: dict[str, Any]) -> bool:
    return payload.get("typ") == "refresh" and isinstance(payload.get("jti"), str)


def create_totp_challenge_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.totp_challenge_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "typ": "totp_challenge",
        "jti": uuid4().hex,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def is_totp_challenge_payload(payload: dict[str, Any]) -> bool:
    return payload.get("typ") == "totp_challenge" and isinstance(payload.get("sub"), str)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
