"""User role definitions and helpers."""

from typing import Literal

StoredRole = Literal["user", "admin", "kent", "rodnulka", "customer"]
TerminalRole = Literal["guest", "user", "admin", "kent", "rodnulka", "customer"]

STORED_ROLES: tuple[StoredRole, ...] = ("user", "admin", "kent", "rodnulka", "customer")

ROLE_LABELS: dict[StoredRole, str] = {
    "user": "Пользователь",
    "admin": "Администратор",
    "kent": "Кент",
    "rodnulka": "Роднулька",
    "customer": "Заказчик",
}

_ROLE_LEVEL: dict[TerminalRole, int] = {
    "guest": 0,
    "user": 1,
    "kent": 1,
    "rodnulka": 1,
    "customer": 1,
    "admin": 2,
}


def is_valid_stored_role(value: str) -> bool:
    return value in STORED_ROLES


def sync_admin_flag(role: str) -> bool:
    """Keep legacy is_admin flag aligned with role."""
    return role == "admin"


def terminal_role_for_user(*, is_authenticated: bool, role: str, is_admin: bool) -> TerminalRole:
    """Map stored user record to terminal RBAC role."""
    if not is_authenticated:
        return "guest"
    if is_admin or role == "admin":
        return "admin"
    if role in STORED_ROLES:
        return role  # type: ignore[return-value]
    return "user"


def role_level(role: TerminalRole) -> int:
    return _ROLE_LEVEL[role]
