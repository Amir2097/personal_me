"""TOTP helpers for 2FA."""

import pyotp


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(*, secret: str, email: str, issuer: str = "Цифровое Сукно") -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    normalized = code.strip().replace(" ", "")
    if not normalized.isdigit() or len(normalized) != 6:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(normalized, valid_window=1)
