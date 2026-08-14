"""Authentication service for Sukno accounts."""

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import HTTPException, status
from jose import JWTError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.roles import can_use_totp, is_valid_role, role_at_least
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_totp_challenge_token,
    decode_token,
    get_password_hash,
    is_refresh_payload,
    is_totp_challenge_payload,
    verify_password,
)
from app.core.totp import generate_secret, provisioning_uri, verify_code
from app.models.sukno_email_verification_token import SuknoEmailVerificationToken
from app.models.sukno_password_reset_token import SuknoPasswordResetToken
from app.models.sukno_refresh_token import SuknoRefreshToken
from app.models.sukno_user import SuknoUser
from app.schemas.auth import (
    LoginResponse,
    PasswordResetTokenResponse,
    RegisterResponse,
    ResendVerificationResponse,
    TokenResponse,
    TotpSetupResponse,
    TotpStatusResponse,
    UserProfile,
)
from app.services.email_service import (
    is_smtp_configured,
    send_password_reset_email,
    send_verification_email,
)


def user_to_profile(user: SuknoUser) -> UserProfile:
    return UserProfile(
        username=user.username,
        email=user.email,
        role=user.role,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        location=user.location,
        telegram=user.telegram,
        email_verified=user.email_verified,
        is_active=user.is_active,
        totp_enabled=user.totp_enabled,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def _find_user_by_login(session: Session, login: str) -> SuknoUser | None:
    user = session.exec(select(SuknoUser).where(SuknoUser.username == login)).first()
    if user:
        return user
    if "@" in login:
        return session.exec(select(SuknoUser).where(SuknoUser.email == login)).first()
    return None


def ensure_initial_admin(session: Session) -> None:
    existing = session.exec(
        select(SuknoUser).where(SuknoUser.username == settings.initial_admin_username)
    ).first()
    if existing:
        changed = False
        if existing.role != "admin":
            existing.role = "admin"
            changed = True
        if not existing.email_verified:
            existing.email_verified = True
            changed = True
        if settings.initial_admin_email and existing.email != settings.initial_admin_email:
            existing.email = settings.initial_admin_email
            changed = True
        if changed:
            session.add(existing)
            session.commit()
        return

    session.add(
        SuknoUser(
            username=settings.initial_admin_username,
            email=settings.initial_admin_email or f"{settings.initial_admin_username}@localhost",
            hashed_password=get_password_hash(settings.initial_admin_password),
            role="admin",
            email_verified=True,
            display_name="Администратор",
        )
    )
    session.commit()


def _issue_token_pair(session: Session, user: SuknoUser) -> TokenResponse:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован.",
        )
    access_token = create_access_token(user.username, token_type="access")
    refresh_token, jti, expires_at = create_refresh_token(user.username)
    session.add(
        SuknoRefreshToken(
            jti=jti,
            username=user.username,
            expires_at=expires_at,
            revoked=False,
        )
    )
    session.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        username=user.username,
        role=user.role,
        email_verified=user.email_verified,
    )


def _create_verification_token(session: Session, username: str) -> str:
    verify_token = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.email_verification_expire_minutes
    )
    session.add(
        SuknoEmailVerificationToken(
            token=verify_token,
            username=username,
            expires_at=expires_at,
            used=False,
        )
    )
    session.commit()
    return verify_token


def _send_verification_for_user(session: Session, user: SuknoUser) -> str:
    verify_token = _create_verification_token(session, user.username)
    if is_smtp_configured():
        verify_url = (
            f"{settings.frontend_base_url.rstrip('/')}"
            f"/auth/verify-email?token={verify_token}"
        )
        send_verification_email(
            user.email,
            verify_url,
            settings.email_verification_expire_minutes,
        )
    return verify_token


def register_user(
    session: Session,
    username: str,
    password: str,
    email: str,
    *,
    accept_terms: bool,
) -> RegisterResponse:
    if not accept_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо согласие с политикой конфиденциальности.",
        )
    if not settings.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Регистрация отключена.",
        )
    if session.exec(select(SuknoUser).where(SuknoUser.username == username)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Имя пользователя уже занято.",
        )
    if session.exec(select(SuknoUser).where(SuknoUser.email == email)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email уже используется.",
        )

    user = SuknoUser(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        role="player",
        email_verified=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    verify_token = _send_verification_for_user(session, user)
    expose = settings.expose_verification_token and not is_smtp_configured()

    if settings.require_email_verification:
        return RegisterResponse(
            message="Аккаунт создан. Подтвердите email, затем войдите.",
            username=username,
            verification_required=True,
            verification_token=verify_token if expose else None,
        )

    tokens = _issue_token_pair(session, user)
    return RegisterResponse(
        message="Аккаунт создан.",
        username=username,
        verification_required=False,
        verification_token=verify_token if expose else None,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )


def login_user(session: Session, login: str, password: str) -> LoginResponse:
    user = _find_user_by_login(session, login)
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
    if settings.require_email_verification and not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Подтвердите email перед входом.",
        )

    if user.totp_enabled and can_use_totp(user.role):
        return LoginResponse(
            requires_totp=True,
            challenge_token=create_totp_challenge_token(user.username),
            username=user.username,
            role=user.role,
            email_verified=user.email_verified,
        )

    user.last_login_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    tokens = _issue_token_pair(session, user)
    return LoginResponse(
        requires_totp=False,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        username=tokens.username,
        role=tokens.role,
        email_verified=tokens.email_verified,
    )


def refresh_user_tokens(session: Session, refresh_token: str) -> TokenResponse:
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
    stored = session.exec(select(SuknoRefreshToken).where(SuknoRefreshToken.jti == jti)).first()
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
    user = session.exec(select(SuknoUser).where(SuknoUser.username == stored.username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден.",
        )
    stored.revoked = True
    session.add(stored)
    session.commit()
    return _issue_token_pair(session, user)


def logout_user(session: Session, refresh_token: str) -> None:
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
    stored = session.exec(select(SuknoRefreshToken).where(SuknoRefreshToken.jti == jti)).first()
    if stored:
        stored.revoked = True
        session.add(stored)
        session.commit()


def revoke_user_refresh_tokens(session: Session, username: str) -> None:
    tokens = session.exec(
        select(SuknoRefreshToken).where(
            SuknoRefreshToken.username == username,
            SuknoRefreshToken.revoked == False,  # noqa: E712
        )
    ).all()
    for item in tokens:
        item.revoked = True
        session.add(item)
    session.commit()


def verify_email(session: Session, token: str) -> UserProfile:
    stored = session.exec(
        select(SuknoEmailVerificationToken).where(SuknoEmailVerificationToken.token == token)
    ).first()
    if (
        not stored
        or stored.used
        or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Токен подтверждения недействителен или истёк.",
        )
    user = session.exec(select(SuknoUser).where(SuknoUser.username == stored.username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )
    user.email_verified = True
    stored.used = True
    session.add(user)
    session.add(stored)
    session.commit()
    session.refresh(user)
    return user_to_profile(user)


def resend_verification(session: Session, login: str) -> ResendVerificationResponse:
    user = _find_user_by_login(session, login)
    generic = "Если аккаунт существует и email не подтверждён, письмо отправлено."
    if not user or user.email_verified:
        return ResendVerificationResponse(message=generic)

    verify_token = _send_verification_for_user(session, user)
    expose = settings.expose_verification_token and not is_smtp_configured()
    return ResendVerificationResponse(
        message=generic,
        verification_token=verify_token if expose else None,
    )


def request_password_reset(session: Session, login: str) -> PasswordResetTokenResponse:
    user = _find_user_by_login(session, login)
    generic = "Если аккаунт существует, инструкции по сбросу будут отправлены."
    if not user:
        return PasswordResetTokenResponse(
            message=generic,
            reset_token=None,
            expires_in_minutes=settings.password_reset_expire_minutes,
        )

    reset_token = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_expire_minutes
    )
    session.add(
        SuknoPasswordResetToken(
            token=reset_token,
            username=user.username,
            expires_at=expires_at,
            used=False,
        )
    )
    session.commit()

    email_sent = False
    if is_smtp_configured():
        reset_url = (
            f"{settings.frontend_base_url.rstrip('/')}"
            f"/auth/reset-password?token={reset_token}"
        )
        try:
            send_password_reset_email(
                user.email,
                reset_url,
                settings.password_reset_expire_minutes,
            )
            email_sent = True
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Не удалось отправить письмо. Попробуйте позже.",
            ) from exc

    expose = settings.expose_reset_token and not email_sent
    return PasswordResetTokenResponse(
        message=generic,
        reset_token=reset_token if expose else None,
        expires_in_minutes=settings.password_reset_expire_minutes,
    )


def confirm_password_reset(session: Session, token: str, new_password: str) -> None:
    stored = session.exec(
        select(SuknoPasswordResetToken).where(SuknoPasswordResetToken.token == token)
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
    user = session.exec(select(SuknoUser).where(SuknoUser.username == stored.username)).first()
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
    user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
    if not user or not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Текущий пароль указан неверно.",
        )
    user.hashed_password = get_password_hash(new_password)
    session.add(user)
    session.commit()
    revoke_user_refresh_tokens(session, user.username)


def get_user_profile(session: Session, username: str) -> UserProfile:
    user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )
    return user_to_profile(user)


def update_user_profile(
    session: Session,
    username: str,
    *,
    display_name: str | None = None,
    bio: str | None = None,
    location: str | None = None,
    telegram: str | None = None,
) -> UserProfile:
    user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )
    if display_name is not None:
        user.display_name = display_name
    if bio is not None:
        user.bio = bio
    if location is not None:
        user.location = location
    if telegram is not None:
        handle = telegram.lstrip("@")
        user.telegram = handle
    session.add(user)
    session.commit()
    session.refresh(user)
    return user_to_profile(user)


def list_users(session: Session) -> list[UserProfile]:
    users = session.exec(select(SuknoUser).order_by(SuknoUser.created_at)).all()
    return [user_to_profile(user) for user in users]


def admin_update_user(
    session: Session,
    username: str,
    *,
    role: str | None,
    is_active: bool | None,
    display_name: str | None,
    actor_username: str,
) -> UserProfile:
    user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден.",
        )
    if username == actor_username and is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя заблокировать свой аккаунт.",
        )

    changes: dict[str, dict[str, object]] = {}
    if role is not None:
        if not is_valid_role(role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недопустимая роль.",
            )
        if username == actor_username and role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя снять с себя роль администратора.",
            )
        if role != user.role:
            changes["role"] = {"from": user.role, "to": role}
        user.role = role
    if is_active is not None:
        if is_active != user.is_active:
            changes["is_active"] = {"from": user.is_active, "to": is_active}
        user.is_active = is_active
    if display_name is not None:
        if display_name != user.display_name:
            changes["display_name"] = {"from": user.display_name, "to": display_name}
        user.display_name = display_name
    session.add(user)
    session.commit()
    session.refresh(user)
    if is_active is False:
        revoke_user_refresh_tokens(session, user.username)

    from app.services import audit_service

    audit_service.record_user_update(
        session,
        actor_username=actor_username,
        target_username=username,
        changes=changes,
    )
    return user_to_profile(user)


def _require_totp_eligible(user: SuknoUser) -> None:
    if not can_use_totp(user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA доступна операторам и администраторам.",
        )


def get_totp_status(user: SuknoUser) -> TotpStatusResponse:
    eligible = can_use_totp(user.role)
    return TotpStatusResponse(
        eligible=eligible,
        enabled=bool(user.totp_enabled),
        pending_setup=eligible and bool(user.totp_secret) and not user.totp_enabled,
    )


def setup_totp(session: Session, user: SuknoUser) -> TotpSetupResponse:
    _require_totp_eligible(user)
    secret = generate_secret()
    user.totp_secret = secret
    user.totp_enabled = False
    session.add(user)
    session.commit()
    return TotpSetupResponse(
        secret=secret,
        otpauth_url=provisioning_uri(
            secret=secret,
            email=user.email,
            issuer=settings.totp_issuer,
        ),
    )


def enable_totp(session: Session, user: SuknoUser, code: str) -> TotpStatusResponse:
    _require_totp_eligible(user)
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала запросите настройку 2FA.",
        )
    if not verify_code(user.totp_secret, code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код подтверждения.",
        )
    user.totp_enabled = True
    session.add(user)
    session.commit()
    session.refresh(user)

    from app.services import audit_service

    audit_service.record(
        session,
        actor_username=user.username,
        action="admin.totp.enable",
        target=user.username,
        details={},
    )
    return get_totp_status(user)


def disable_totp(session: Session, user: SuknoUser, password: str, code: str) -> TotpStatusResponse:
    _require_totp_eligible(user)
    if not user.totp_enabled or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA не включена.",
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль.",
        )
    if not verify_code(user.totp_secret, code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код подтверждения.",
        )
    user.totp_secret = ""
    user.totp_enabled = False
    session.add(user)
    session.commit()
    revoke_user_refresh_tokens(session, user.username)

    from app.services import audit_service

    audit_service.record(
        session,
        actor_username=user.username,
        action="admin.totp.disable",
        target=user.username,
        details={},
    )
    return get_totp_status(user)


def verify_totp_login(session: Session, challenge_token: str, code: str) -> TokenResponse:
    try:
        payload = decode_token(challenge_token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия 2FA истекла. Войдите снова.",
        ) from exc
    if not is_totp_challenge_payload(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный challenge-токен.",
        )
    username = payload.get("sub")
    if not isinstance(username, str) or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный challenge-токен.",
        )
    user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
    if (
        not user
        or not user.is_active
        or not user.totp_enabled
        or not user.totp_secret
        or not can_use_totp(user.role)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA недоступна для этого аккаунта.",
        )
    if not verify_code(user.totp_secret, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный код 2FA.",
        )
    user.last_login_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    return _issue_token_pair(session, user)
