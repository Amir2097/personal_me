"""Shared API dependencies."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.config import settings
from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE
from app.core.db import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=False,
)


def get_optional_access_token(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
) -> str | None:
    """JWT из Authorization header или httpOnly cookie."""
    if bearer_token:
        return bearer_token
    cookie_token = request.cookies.get(ACCESS_COOKIE)
    if cookie_token:
        return cookie_token
    return None


def get_optional_refresh_token(
    request: Request,
    body_refresh_token: str | None = None,
) -> str | None:
    """Refresh token из cookie или тела запроса."""
    if body_refresh_token:
        return body_refresh_token
    return request.cookies.get(REFRESH_COOKIE)


def _username_from_token(token: str) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        username = payload.get("sub")
        if not isinstance(username, str):
            raise credentials_exception
        return username
    except JWTError as exc:
        raise credentials_exception from exc


def get_current_username(
    token: str | None = Depends(get_optional_access_token),
) -> str:
    """Extract username from JWT token."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _username_from_token(token)


def get_current_username_from_token(token: str) -> str:
    """Extract username from token string."""
    return _username_from_token(token)


def get_current_admin_user(
    username: str = Depends(get_current_username),
    session: Session = Depends(get_session),
) -> User:
    """Проверить, что текущий пользователь — администратор."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для администратора.",
        )
    return user
