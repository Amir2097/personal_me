"""Authentication service layer."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from jose import JWTError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    is_refresh_payload,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenResponse


def ensure_initial_admin(session: Session) -> None:
    """Create initial admin user if it does not exist."""
    existing = session.exec(
        select(User).where(User.username == settings.initial_admin_username)
    ).first()
    if existing:
        return
    user = User(
        username=settings.initial_admin_username,
        hashed_password=get_password_hash(settings.initial_admin_password),
    )
    session.add(user)
    session.commit()


def issue_token_pair(session: Session, username: str) -> TokenResponse:
    """Create access/refresh tokens and persist refresh token metadata."""
    access_token = create_access_token(username)
    refresh_token, jti, expires_at = create_refresh_token(username)
    session.add(
        RefreshToken(
            jti=jti,
            username=username,
            expires_at=expires_at,
            revoked=False,
        )
    )
    session.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def login_user(session: Session, username: str, password: str) -> TokenResponse:
    """Validate user credentials and issue token pair."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    return issue_token_pair(session, username=user.username)


def register_user(session: Session, username: str, password: str) -> TokenResponse:
    """Create a new user and return token pair."""
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )
    new_user = User(username=username, hashed_password=get_password_hash(password))
    session.add(new_user)
    session.commit()
    return issue_token_pair(session, username=username)


def refresh_user_tokens(session: Session, refresh_token: str) -> TokenResponse:
    """Rotate token pair based on valid refresh token."""
    try:
        payload = decode_token(refresh_token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc
    if not is_refresh_payload(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )
    username = payload.get("sub")
    jti = payload.get("jti")
    stored = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    if (
        not stored
        or stored.revoked
        or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
        or stored.username != username
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is revoked or expired.",
        )
    stored.revoked = True
    session.add(stored)
    session.commit()
    return issue_token_pair(session, username=stored.username)


def logout_user(session: Session, refresh_token: str) -> None:
    """Revoke a refresh token to complete logout."""
    try:
        payload = decode_token(refresh_token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc
    if not is_refresh_payload(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )
    jti = payload.get("jti")
    stored = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    if stored:
        stored.revoked = True
        session.add(stored)
        session.commit()
