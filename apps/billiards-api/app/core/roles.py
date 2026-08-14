"""Role definitions for Цифровое Сукно accounts."""

from typing import Literal

SuknoRole = Literal["player", "operator", "admin"]

STORED_ROLES: tuple[SuknoRole, ...] = ("player", "operator", "admin")

ROLE_LABELS: dict[SuknoRole, str] = {
    "player": "Игрок",
    "operator": "Оператор",
    "admin": "Администратор",
}

_ROLE_LEVEL: dict[SuknoRole, int] = {
    "player": 1,
    "operator": 2,
    "admin": 3,
}


def is_valid_role(value: str) -> bool:
    return value in STORED_ROLES


def role_level(role: str) -> int:
    if role in _ROLE_LEVEL:
        return _ROLE_LEVEL[role]  # type: ignore[index]
    return 0


def role_at_least(role: str, minimum: SuknoRole) -> bool:
    return role_level(role) >= role_level(minimum)


def can_use_totp(role: str) -> bool:
    return role_at_least(role, "operator")


def can_sync_room(source: str, role: str | None) -> bool:
    """TV/host sync: device, hub SSO, or Sukno operator/admin."""
    if source in ("device", "hub", "legacy_admin"):
        return True
    if source == "account" and role:
        return role_at_least(role, "operator")
    return False
