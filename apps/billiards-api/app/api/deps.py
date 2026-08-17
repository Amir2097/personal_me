"""Auth dependencies: Sukno accounts, hub JWT, device JWT, legacy admin key."""

from dataclasses import dataclass
from secrets import compare_digest

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.cookies import SUKNO_ACCESS_COOKIE, SUKNO_REFRESH_COOKIE
from app.core.db import get_session
from app.core.roles import can_report_cup_score, can_sync_room, role_at_least
from app.core.security import create_access_token, decode_token
from app.models.sukno_user import SuknoUser

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/billiards/auth/login",
    auto_error=False,
)


def get_optional_access_token(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
) -> str | None:
    if bearer_token:
        return bearer_token
    return request.cookies.get(SUKNO_ACCESS_COOKIE)


def get_optional_refresh_token(
    request: Request,
    body_refresh_token: str | None = None,
) -> str | None:
    if body_refresh_token:
        return body_refresh_token
    return request.cookies.get(SUKNO_REFRESH_COOKIE)


def _username_from_token(token: str) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not isinstance(username, str) or not username:
            raise credentials_exception
        return username
    except JWTError as exc:
        raise credentials_exception from exc


def get_current_username(
    token: str | None = Depends(get_optional_access_token),
) -> str:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _username_from_token(token)


def issue_access_token(
    username: str,
    token_type: str = "device",
    expire_minutes: int | None = None,
) -> str:
    if expire_minutes is not None:
        from datetime import datetime, timedelta, timezone
        from uuid import uuid4

        from jose import jwt

        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        return jwt.encode(
            {
                "sub": username,
                "exp": expire,
                "typ": token_type,
                "jti": uuid4().hex,
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
    return create_access_token(username, token_type=token_type)


@dataclass
class AuthIdentity:
    username: str
    source: str
    role: str | None = None
    email_verified: bool | None = None


def resolve_identity(session: Session, username: str) -> AuthIdentity:
    if username.startswith("local_"):
        return AuthIdentity(username=username, source="device")
    if username == ADMIN_SUB:
        return AuthIdentity(
            username=username,
            source="legacy_admin",
            role="admin",
            email_verified=True,
        )

    user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
    if user:
        return AuthIdentity(
            username=user.username,
            source="account",
            role=user.role,
            email_verified=user.email_verified,
        )
    return AuthIdentity(username=username, source="hub")


@dataclass
class GameActor:
    username: str
    source: str
    role: str | None = None


def get_game_actor(
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username),
) -> GameActor:
    identity = resolve_identity(session, username)
    return GameActor(
        username=identity.username,
        source=identity.source,
        role=identity.role,
    )


def require_sync_actor(
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username),
) -> GameActor:
    identity = resolve_identity(session, username)
    if not can_sync_room(identity.source, identity.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вести трансляцию на табло могут только оператор или администратор. Просмотр по ссылке доступен всем.",
        )
    return GameActor(
        username=identity.username,
        source=identity.source,
        role=identity.role,
    )


def require_account_actor(
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username),
) -> GameActor:
    identity = resolve_identity(session, username)
    if not can_report_cup_score(identity.source):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Чтобы внести результат, войдите в аккаунт Цифрового Сукна.",
        )
    return GameActor(
        username=identity.username,
        source=identity.source,
        role=identity.role,
    )


def get_current_sukno_user(
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username),
) -> SuknoUser:
    user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется аккаунт Цифрового Сукна.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован.",
        )
    return user


def require_role(minimum_role: str):
    def _dependency(
        session: Session = Depends(get_session),
        username: str = Depends(get_current_username),
    ) -> SuknoUser:
        identity = resolve_identity(session, username)
        if identity.source == "legacy_admin":
            admin_user = session.exec(
                select(SuknoUser).where(SuknoUser.username == settings.initial_admin_username)
            ).first()
            if admin_user:
                return admin_user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Legacy admin key без аккаунта — войдите как admin.",
            )

        user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав.",
            )
        if not role_at_least(user.role, minimum_role):  # type: ignore[arg-type]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав.",
            )
        return user

    return _dependency


def _key_matches(given: str, expected: str) -> bool:
    if not expected:
        return False
    left = given.encode("utf-8")
    right = expected.encode("utf-8")
    if len(left) != len(right):
        compare_digest(right, right)
        return False
    return compare_digest(left, right)


ADMIN_SUB = "sukno_admin"


def legacy_admin_enabled() -> bool:
    return settings.allow_legacy_admin_key and bool(settings.sukno_admin_key.strip())


def legacy_admin_disabled() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Legacy admin key отключён. Войдите аккаунтом с ролью admin.",
    )


def _admin_unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin access required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_admin(
    request: Request,
    session: Session = Depends(get_session),
    token: str | None = Depends(get_optional_access_token),
) -> str:
    if legacy_admin_enabled():
        expected = settings.sukno_admin_key.strip()
        header_key = request.headers.get("x-sukno-admin-key", "")
        if header_key and _key_matches(header_key, expected):
            return ADMIN_SUB

    if token is None:
        raise _admin_unauthorized()

    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise _admin_unauthorized() from exc

    username = payload.get("sub")
    token_type = payload.get("typ")
    if not isinstance(username, str) or not username:
        raise _admin_unauthorized()

    if token_type == "admin" and username == ADMIN_SUB:
        if not legacy_admin_enabled():
            raise legacy_admin_disabled()
        return ADMIN_SUB

    if token_type == "access":
        user = session.exec(select(SuknoUser).where(SuknoUser.username == username)).first()
        if user and user.is_active and user.role == "admin":
            if settings.require_email_verification and not user.email_verified:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Подтвердите email администратора.",
                )
            return user.username

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin session required",
    )


def unlock_admin_session(key: str) -> str:
    if not legacy_admin_enabled():
        raise legacy_admin_disabled()
    expected = settings.sukno_admin_key.strip()
    if not _key_matches(key, expected):
        raise _admin_unauthorized()
    return issue_access_token(ADMIN_SUB, token_type="admin", expire_minutes=60 * 12)
