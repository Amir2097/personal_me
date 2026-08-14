"""Account and device identity for Цифровое Сукно."""

from uuid import uuid4

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from sqlmodel import Session

from app.api.deps import (
    get_current_sukno_user,
    get_current_username,
    get_optional_refresh_token,
    issue_access_token,
    legacy_admin_disabled,
    legacy_admin_enabled,
    resolve_identity,
)
from app.core.cookies import clear_auth_cookies, set_account_cookies, set_device_access_cookie
from app.core.db import get_session
from app.core.rate_limit import check_auth_rate_limit
from app.schemas.auth import (
    AuthConfigResponse,
    ChangePasswordRequest,
    DeviceAuthRequest,
    DeviceAuthResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetTokenResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    TokenResponse,
    TotpDisableRequest,
    TotpEnableRequest,
    TotpSetupResponse,
    TotpStatusResponse,
    TotpVerifyRequest,
    UserProfile,
    UserProfileUpdate,
    VerifyEmailRequest,
)
from app.services import auth_service
from app.services.avatar_service import remove_user_avatar, save_avatar_upload
from app.services.email_service import is_smtp_configured

router = APIRouter(prefix="/billiards/auth", tags=["billiards-auth"])


def _clean_device_id(raw: str) -> str:
    value = "".join(ch for ch in raw.strip().lower() if ch.isalnum() or ch in "-_")
    return value[:64] or uuid4().hex


@router.get("/config", response_model=AuthConfigResponse, summary="Публичные настройки auth")
def auth_config() -> AuthConfigResponse:
    from app.core.config import settings

    return AuthConfigResponse(
        allow_registration=settings.allow_registration,
        require_email_verification=settings.require_email_verification,
        expose_reset_token=settings.expose_reset_token,
        expose_verification_token=settings.expose_verification_token,
        password_reset_via_email=is_smtp_configured(),
        email_verification_via_email=is_smtp_configured(),
        allow_legacy_admin_key=settings.allow_legacy_admin_key and bool(settings.sukno_admin_key.strip()),
    )


@router.post("/register", response_model=RegisterResponse, summary="Регистрация аккаунта")
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> RegisterResponse:
    check_auth_rate_limit(request)
    result = auth_service.register_user(
        session,
        payload.username,
        payload.password,
        payload.email,
        accept_terms=payload.accept_terms,
    )
    if result.access_token and result.refresh_token:
        set_account_cookies(
            response,
            TokenResponse(
                access_token=result.access_token,
                refresh_token=result.refresh_token,
                username=result.username,
            ),
        )
    return result


@router.post("/login", response_model=LoginResponse, summary="Вход")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> LoginResponse:
    check_auth_rate_limit(request)
    result = auth_service.login_user(session, payload.username, payload.password)
    if not result.requires_totp and result.access_token and result.refresh_token:
        set_account_cookies(
            response,
            TokenResponse(
                access_token=result.access_token,
                refresh_token=result.refresh_token,
                username=result.username,
                role=result.role,
                email_verified=result.email_verified,
            ),
        )
    return result


@router.post("/totp/verify", response_model=TokenResponse, summary="Подтвердить вход 2FA")
def verify_totp_login(
    payload: TotpVerifyRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> TokenResponse:
    check_auth_rate_limit(request)
    tokens = auth_service.verify_totp_login(session, payload.challenge_token, payload.code)
    set_account_cookies(response, tokens)
    return tokens


@router.get("/totp/status", response_model=TotpStatusResponse, summary="Статус 2FA")
def totp_status(user=Depends(get_current_sukno_user)) -> TotpStatusResponse:
    return auth_service.get_totp_status(user)


@router.post("/totp/setup", response_model=TotpSetupResponse, summary="Начать настройку 2FA")
def totp_setup(
    session: Session = Depends(get_session),
    user=Depends(get_current_sukno_user),
) -> TotpSetupResponse:
    return auth_service.setup_totp(session, user)


@router.post("/totp/enable", response_model=TotpStatusResponse, summary="Включить 2FA")
def totp_enable(
    payload: TotpEnableRequest,
    session: Session = Depends(get_session),
    user=Depends(get_current_sukno_user),
) -> TotpStatusResponse:
    return auth_service.enable_totp(session, user, payload.code)


@router.post("/totp/disable", response_model=TotpStatusResponse, summary="Отключить 2FA")
def totp_disable(
    payload: TotpDisableRequest,
    session: Session = Depends(get_session),
    user=Depends(get_current_sukno_user),
) -> TotpStatusResponse:
    return auth_service.disable_totp(session, user, payload.password, payload.code)


@router.post("/refresh", response_model=TokenResponse, summary="Обновить токены")
def refresh(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    session: Session = Depends(get_session),
) -> TokenResponse:
    from fastapi import HTTPException, status

    body_token = payload.refresh_token if payload else None
    token = get_optional_refresh_token(request, body_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh-токен не найден.",
        )
    tokens = auth_service.refresh_user_tokens(session, token)
    set_account_cookies(response, tokens)
    return tokens


@router.post("/logout", summary="Выход")
def logout(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    body_token = payload.refresh_token if payload else None
    token = get_optional_refresh_token(request, body_token)
    if token:
        auth_service.logout_user(session, token)
    clear_auth_cookies(response)
    return {"message": "ok"}


@router.post("/verify-email", response_model=UserProfile, summary="Подтвердить email")
def verify_email(payload: VerifyEmailRequest, session: Session = Depends(get_session)) -> UserProfile:
    return auth_service.verify_email(session, payload.token)


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    summary="Повторно отправить письмо подтверждения",
)
def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> ResendVerificationResponse:
    check_auth_rate_limit(request)
    return auth_service.resend_verification(session, payload.login)


@router.post(
    "/password-reset/request",
    response_model=PasswordResetTokenResponse,
    summary="Запросить сброс пароля",
)
def password_reset_request(
    payload: PasswordResetRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> PasswordResetTokenResponse:
    check_auth_rate_limit(request)
    return auth_service.request_password_reset(session, payload.login)


@router.post("/password-reset/confirm", summary="Подтвердить новый пароль")
def password_reset_confirm(
    payload: PasswordResetConfirm,
    response: Response,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    auth_service.confirm_password_reset(session, payload.token, payload.new_password)
    clear_auth_cookies(response)
    return {"message": "Пароль обновлён."}


@router.post("/change-password", summary="Сменить пароль")
def change_password_route(
    payload: ChangePasswordRequest,
    response: Response,
    session: Session = Depends(get_session),
    user=Depends(get_current_sukno_user),
) -> dict[str, str]:
    auth_service.change_password(
        session,
        user.username,
        payload.current_password,
        payload.new_password,
    )
    clear_auth_cookies(response)
    return {"message": "Пароль обновлён."}


@router.get("/profile", response_model=UserProfile, summary="Профиль аккаунта")
def read_profile(
    session: Session = Depends(get_session),
    user=Depends(get_current_sukno_user),
) -> UserProfile:
    return auth_service.get_user_profile(session, user.username)


@router.patch("/profile", response_model=UserProfile, summary="Обновить профиль")
def patch_profile(
    payload: UserProfileUpdate,
    session: Session = Depends(get_session),
    user=Depends(get_current_sukno_user),
) -> UserProfile:
    return auth_service.update_user_profile(
        session,
        user.username,
        display_name=payload.display_name,
        bio=payload.bio,
        location=payload.location,
        telegram=payload.telegram,
    )


@router.post("/avatar", response_model=UserProfile, summary="Загрузить аватар")
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_sukno_user),
    session: Session = Depends(get_session),
) -> UserProfile:
    return await save_avatar_upload(session, user, file)


@router.delete("/avatar", response_model=UserProfile, summary="Удалить аватар")
def delete_avatar(
    user=Depends(get_current_sukno_user),
    session: Session = Depends(get_session),
) -> UserProfile:
    return remove_user_avatar(session, user)


@router.post("/device", response_model=DeviceAuthResponse, summary="Выдать локальный токен устройства")
def create_device_session(payload: DeviceAuthRequest, response: Response) -> DeviceAuthResponse:
    device_id = _clean_device_id(payload.device_id)
    username = f"local_{device_id[:16]}"
    token = issue_access_token(username, token_type="device")
    set_device_access_cookie(response, token)
    return DeviceAuthResponse(access_token=token, username=username, device_id=device_id)


@router.get("/me", response_model=MeResponse, summary="Текущий оператор Цифрового Сукна")
def read_me(
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username),
) -> MeResponse:
    identity = resolve_identity(session, username)
    if identity.source == "legacy_admin" and not legacy_admin_enabled():
        raise legacy_admin_disabled()
    is_admin = identity.role == "admin" or identity.source == "legacy_admin"
    display_name = None
    email = None
    avatar_url = None
    if identity.source == "account":
        user = auth_service.get_user_profile(session, username)
        display_name = user.display_name
        email = user.email
        avatar_url = user.avatar_url or None
    return MeResponse(
        username=username,
        source=identity.source,
        role=identity.role,
        email=email,
        email_verified=identity.email_verified,
        display_name=display_name,
        avatar_url=avatar_url,
        is_admin=is_admin,
    )
