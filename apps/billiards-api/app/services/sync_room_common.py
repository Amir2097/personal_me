"""Shared helpers for kolkhoz/cup sync rooms."""

from datetime import datetime, timedelta, timezone
from secrets import choice
from string import ascii_uppercase, digits

from app.core.config import settings

_CODE_ALPHABET = "".join(c for c in ascii_uppercase + digits if c not in "O0IL1")


def generate_room_code(length: int | None = None) -> str:
    n = length or settings.sync_room_code_length
    return "".join(choice(_CODE_ALPHABET) for _ in range(n))


def new_room_expires_at() -> datetime | None:
    """Return expiry for a new/extended room, or None when TTL disabled."""
    hours = settings.sync_room_ttl_hours
    if hours <= 0:
        return None
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def is_room_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    normalized = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
    return normalized <= datetime.now(timezone.utc)
