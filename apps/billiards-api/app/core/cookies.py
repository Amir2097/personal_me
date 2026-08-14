"""HTTP-only cookie helpers for Цифровое Сукно JWT auth."""

from fastapi import Response

from app.core.config import settings
from app.schemas.auth import TokenResponse

SUKNO_ACCESS_COOKIE = "sukno_access_token"
SUKNO_REFRESH_COOKIE = "sukno_refresh_token"


def _cookie_kwargs() -> dict:
    kwargs: dict = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
        "path": settings.auth_cookie_path,
    }
    if settings.cookie_domain:
        kwargs["domain"] = settings.cookie_domain
    return kwargs


def set_account_cookies(response: Response, tokens: TokenResponse) -> None:
    """Set access/refresh tokens in httpOnly cookies for Sukno accounts."""
    access_max_age = settings.access_token_expire_minutes * 60
    refresh_max_age = settings.refresh_token_expire_days * 24 * 60 * 60
    cookie_kwargs = _cookie_kwargs()

    response.set_cookie(
        key=SUKNO_ACCESS_COOKIE,
        value=tokens.access_token,
        max_age=access_max_age,
        **cookie_kwargs,
    )
    response.set_cookie(
        key=SUKNO_REFRESH_COOKIE,
        value=tokens.refresh_token,
        max_age=refresh_max_age,
        **cookie_kwargs,
    )


def set_device_access_cookie(response: Response, access_token: str) -> None:
    """Device sessions: access token only (no refresh rotation)."""
    cookie_kwargs = _cookie_kwargs()
    response.set_cookie(
        key=SUKNO_ACCESS_COOKIE,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        **cookie_kwargs,
    )


def clear_auth_cookies(response: Response) -> None:
    """Remove Sukno auth cookies."""
    cookie_kwargs = _cookie_kwargs()
    response.delete_cookie(SUKNO_ACCESS_COOKIE, **cookie_kwargs)
    response.delete_cookie(SUKNO_REFRESH_COOKIE, **cookie_kwargs)
