"""HTTP-only cookie helpers for JWT auth."""

from fastapi import Response

from app.core.config import settings
from app.schemas.auth import TokenResponse

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


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


def set_auth_cookies(response: Response, tokens: TokenResponse) -> None:
    """Установить access/refresh токены в httpOnly cookies."""
    access_max_age = settings.access_token_expire_minutes * 60
    refresh_max_age = settings.refresh_token_expire_days * 24 * 60 * 60
    cookie_kwargs = _cookie_kwargs()

    response.set_cookie(
        key=ACCESS_COOKIE,
        value=tokens.access_token,
        max_age=access_max_age,
        **cookie_kwargs,
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=tokens.refresh_token,
        max_age=refresh_max_age,
        **cookie_kwargs,
    )


def clear_auth_cookies(response: Response) -> None:
    """Удалить auth cookies."""
    cookie_kwargs = _cookie_kwargs()
    response.delete_cookie(ACCESS_COOKIE, **cookie_kwargs)
    response.delete_cookie(REFRESH_COOKIE, **cookie_kwargs)
