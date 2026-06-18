"""Simple in-memory rate limiter for auth endpoints."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.core.config import settings

_attempts: dict[str, list[float]] = defaultdict(list)


def check_auth_rate_limit(request: Request) -> None:
    """Ограничить частоту запросов к auth по IP."""
    if settings.auth_rate_limit_per_minute <= 0:
        return

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - 60
    history = [ts for ts in _attempts[client_ip] if ts >= window_start]
    if len(history) >= settings.auth_rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток. Повторите позже.",
        )
    history.append(now)
    _attempts[client_ip] = history
