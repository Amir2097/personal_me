"""Authentication endpoints."""

from fastapi import APIRouter, Depends, Request, Response
from sqlmodel import Session

from app.api.deps import (
    get_current_username,
    get_optional_refresh_token,
)
from app.core.config import settings
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.db import get_session
from app.core.rate_limit import check_auth_rate_limit
from app.schemas.auth import (
    AuthConfigResponse,
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetTokenResponse,
    RefreshTokenRequest,
    RegisterRequest,
    SsoExchangeRequest,
    SsoExchangeResponse,
    TokenResponse,
    UserProfile,
)
from app.services.auth_service import (
    change_password,
    confirm_password_reset,
    get_user_profile,
    login_user,
    logout_user,
    refresh_user_tokens,
    register_user,
    request_password_reset,
)
from app.services.email_service import is_smtp_configured
from app.services.sso_service import exchange_sso_code

router = APIRouter(prefix="/auth", tags=["auth"])


def _resolve_refresh_token(
    request: Request,
    payload: RefreshTokenRequest | None,
) -> str:
    body_token = payload.refresh_token if payload else None
    token = get_optional_refresh_token(request, body_token)
    if not token:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh-токен не найден.",
        )
    return token


@router.get(
    "/config",
    response_model=AuthConfigResponse,
    summary="Публичные настройки auth",
)
def auth_config() -> AuthConfigResponse:
    """Вернуть флаги для UI."""
    return AuthConfigResponse(
        allow_registration=settings.allow_registration,
        expose_reset_token=settings.expose_reset_token,
        password_reset_via_email=is_smtp_configured(),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход и выдача JWT",
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Выдать JWT для валидных учётных данных."""
    check_auth_rate_limit(request)
    tokens = login_user(session, payload.username, payload.password)
    set_auth_cookies(response, tokens)
    return tokens


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Профиль текущего пользователя",
)
def me(
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username),
) -> UserProfile:
    """Получить профиль текущего пользователя."""
    profile_username, is_admin = get_user_profile(session, username)
    return UserProfile(username=profile_username, is_admin=is_admin)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Регистрация пользователя",
)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Зарегистрировать пользователя и выдать токены."""
    check_auth_rate_limit(request)
    tokens = register_user(session, payload.username, payload.password, payload.email)
    set_auth_cookies(response, tokens)
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновление JWT",
)
def refresh(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    payload: RefreshTokenRequest | None = None,
) -> TokenResponse:
    """Обновить пару токенов по refresh-токену."""
    refresh_token = _resolve_refresh_token(request, payload)
    tokens = refresh_user_tokens(session, refresh_token)
    set_auth_cookies(response, tokens)
    return tokens


@router.post(
    "/logout",
    status_code=204,
    summary="Выход из системы",
)
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    payload: RefreshTokenRequest | None = None,
) -> Response:
    """Выйти из системы, отозвав refresh-токен."""
    refresh_token = get_optional_refresh_token(
        request,
        payload.refresh_token if payload else None,
    )
    if refresh_token:
        logout_user(session, refresh_token)
    clear_auth_cookies(response)
    return Response(status_code=204)


@router.post(
    "/sso/exchange",
    response_model=SsoExchangeResponse,
    summary="Обмен SSO-кода",
    description="Сервис обменивает одноразовый код (из go <service>) на access JWT.",
)
def sso_exchange(
    payload: SsoExchangeRequest,
    session: Session = Depends(get_session),
) -> SsoExchangeResponse:
    """Обменять SSO-код на access token."""
    username, access_token = exchange_sso_code(session, payload.code)
    return SsoExchangeResponse(username=username, access_token=access_token)


@router.post(
    "/password-reset/request",
    response_model=PasswordResetTokenResponse,
    summary="Запрос сброса пароля",
)
def password_reset_request(
    payload: PasswordResetRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> PasswordResetTokenResponse:
    """Запросить токен сброса пароля."""
    check_auth_rate_limit(request)
    return request_password_reset(session, payload.username)


@router.post(
    "/password-reset/confirm",
    status_code=204,
    summary="Подтверждение сброса пароля",
)
def password_reset_confirm(
    payload: PasswordResetConfirm,
    session: Session = Depends(get_session),
) -> Response:
    """Подтвердить сброс пароля."""
    confirm_password_reset(session, payload.token, payload.new_password)
    return Response(status_code=204)


@router.post(
    "/change-password",
    status_code=204,
    summary="Смена пароля",
)
def change_user_password(
    payload: ChangePasswordRequest,
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username),
) -> Response:
    """Сменить пароль текущего пользователя."""
    change_password(session, username, payload.current_password, payload.new_password)
    return Response(status_code=204)
