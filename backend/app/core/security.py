"""JWT and password helper utilities."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str) -> str:
    """Create signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "jti": str(uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Create signed JWT refresh token and return token metadata."""
    expire = datetime.now(timezone.utc) + (
        timedelta(days=settings.refresh_token_expire_days)
    )
    jti = str(uuid4())
    payload: dict[str, Any] = {"sub": subject, "type": "refresh", "jti": jti, "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def decode_token(token: str) -> dict[str, Any]:
    """Decode token and return payload."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def is_refresh_payload(payload: dict[str, Any]) -> bool:
    """Check whether payload belongs to refresh token."""
    return payload.get("type") == "refresh" and isinstance(payload.get("jti"), str)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash plain password."""
    return pwd_context.hash(password)
