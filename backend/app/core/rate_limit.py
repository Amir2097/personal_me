"""Simple in-memory rate limiter for auth endpoints."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.core.config import settings

_attempts: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(request: Request, *, limit: int, scope: str) -> None:
    if limit <= 0:
        return

    client_ip = request.client.host if request.client else "unknown"
    key = f"{scope}:{client_ip}"
    now = time.time()
    window_start = now - 60
    history = [ts for ts in _attempts[key] if ts >= window_start]
    if len(history) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток. Повторите позже.",
        )
    history.append(now)
    _attempts[key] = history


def check_auth_rate_limit(request: Request) -> None:
    """Ограничить частоту запросов к auth по IP."""
    _check_rate_limit(
        request,
        limit=settings.auth_rate_limit_per_minute,
        scope="auth",
    )


def check_feedback_rate_limit(request: Request) -> None:
    """Ограничить частоту отправки формы обратной связи по IP."""
    _check_rate_limit(
        request,
        limit=settings.feedback_rate_limit_per_minute,
        scope="feedback",
    )
