"""Authentication service layer."""

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

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
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import PasswordResetTokenResponse, TokenResponse
from app.services.email_service import is_smtp_configured, send_password_reset_email


def _find_user_by_login(session: Session, login: str) -> User | None:
    """Find user by username or email."""
    user = session.exec(select(User).where(User.username == login)).first()
    if user:
        return user
    if "@" in login:
        return session.exec(select(User).where(User.email == login)).first()
    return None


def ensure_initial_admin(session: Session) -> None:
    """Create initial admin user if it does not exist."""
    existing = session.exec(
        select(User).where(User.username == settings.initial_admin_username)
    ).first()
    if existing:
        if not existing.is_admin:
            existing.is_admin = True
            session.add(existing)
        if settings.initial_admin_email and not existing.email:
            existing.email = settings.initial_admin_email
            session.add(existing)
        session.commit()
        return
    user = User(
        username=settings.initial_admin_username,
        hashed_password=get_password_hash(settings.initial_admin_password),
        is_admin=True,
        email=settings.initial_admin_email or None,
    )
    session.add(user)
    session.commit()


def issue_token_pair(session: Session, username: str) -> TokenResponse:
    """Create access/refresh tokens and persist refresh token metadata."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован.",
        )
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
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        username=username,
        is_admin=bool(user and user.is_admin),
    )


def login_user(session: Session, username: str, password: str) -> TokenResponse:
    """Validate user credentials and issue token pair."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован.",
        )
    user.last_login_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    return issue_token_pair(session, username=user.username)


def register_user(
    session: Session,
    username: str,
    password: str,
    email: str | None = None,
    *,
    accept_terms: bool = False,
) -> TokenResponse:
    """Create a new user and return token pair."""
    if not accept_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо согласие с политикой конфиденциальности и пользовательским соглашением.",
        )
    if not settings.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Регистрация отключена.",
        )
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Имя пользователя уже занято.",
        )
    if email:
        email_taken = session.exec(select(User).where(User.email == email)).first()
        if email_taken:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email уже используется.",
            )
    new_user = User(
        username=username,
        hashed_password=get_password_hash(password),
        email=email,
    )
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
            detail="Недействительный refresh-токен.",
        ) from exc
    if not is_refresh_payload(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh-токен.",
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
            detail="Refresh-токен отозван или истёк.",
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
            detail="Недействительный refresh-токен.",
        ) from exc
    if not is_refresh_payload(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh-токен.",
        )
    jti = payload.get("jti")
    stored = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    if stored:
        stored.revoked = True
        session.add(stored)
        session.commit()


def revoke_user_refresh_tokens(session: Session, username: str) -> None:
    """Отозвать все refresh-токены пользователя."""
    tokens = session.exec(
        select(RefreshToken).where(
            RefreshToken.username == username,
            RefreshToken.revoked == False,  # noqa: E712
        )
    ).all()
    for item in tokens:
        item.revoked = True
        session.add(item)
    session.commit()


def request_password_reset(session: Session, username: str) -> PasswordResetTokenResponse:
    """Создать одноразовый токен сброса пароля."""
    user = _find_user_by_login(session, username)
    if not user:
        return PasswordResetTokenResponse(
            message="Если пользователь существует, инструкции по сбросу будут отправлены.",
            reset_token=None,
            expires_in_minutes=settings.password_reset_expire_minutes,
        )

    reset_token = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_expire_minutes
    )
    session.add(
        PasswordResetToken(
            token=reset_token,
            username=user.username,
            expires_at=expires_at,
            used=False,
        )
    )
    session.commit()

    email_sent = False
    if user.email and is_smtp_configured():
        reset_url = (
            f"{settings.oidc_frontend_base_url.rstrip('/')}"
            f"/reset-password?token={reset_token}"
        )
        try:
            send_password_reset_email(
                user.email,
                reset_url,
                settings.password_reset_expire_minutes,
            )
            email_sent = True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Не удалось отправить письмо. Попробуйте позже.",
            ) from None

    if email_sent:
        message = "Если пользователь существует, инструкции по сбросу отправлены на email."
    elif settings.expose_reset_token:
        message = (
            "Токен сброса пароля создан. Используйте reset-password <token> <новый_пароль>."
        )
    else:
        message = "Если пользователь существует, инструкции по сбросу будут отправлены."

    return PasswordResetTokenResponse(
        message=message,
        reset_token=reset_token if settings.expose_reset_token and not email_sent else None,
        expires_in_minutes=settings.password_reset_expire_minutes,
    )


def confirm_password_reset(session: Session, token: str, new_password: str) -> None:
    """Подтвердить сброс пароля по одноразовому токену."""
    stored = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    ).first()
    if (
        not stored
        or stored.used
        or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Токен сброса недействителен или истёк.",
        )

    user = session.exec(select(User).where(User.username == stored.username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )

    user.hashed_password = get_password_hash(new_password)
    stored.used = True
    session.add(user)
    session.add(stored)
    session.commit()
    revoke_user_refresh_tokens(session, user.username)


def change_password(
    session: Session, username: str, current_password: str, new_password: str
) -> None:
    """Сменить пароль авторизованного пользователя."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Текущий пароль указан неверно.",
        )

    user.hashed_password = get_password_hash(new_password)
    session.add(user)
    session.commit()
    revoke_user_refresh_tokens(session, user.username)


def get_user_profile(session: Session, username: str) -> tuple[str, bool, str | None]:
    """Вернуть username, is_admin и email."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )
    return user.username, user.is_admin, user.email


def update_user_profile(
    session: Session, username: str, email: str | None
) -> tuple[str, bool, str | None]:
    """Обновить email пользователя."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )
    if email:
        taken = session.exec(
            select(User).where(User.email == email, User.username != username)
        ).first()
        if taken:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email уже используется.",
            )
    user.email = email or None
    session.add(user)
    session.commit()
    session.refresh(user)
    return user.username, user.is_admin, user.email
