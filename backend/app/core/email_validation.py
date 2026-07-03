"""Shared email normalization helpers."""

from email_validator import EmailNotValidError, validate_email


def normalize_optional_email(value: str | None, *, allow_test_domains: bool = True) -> str | None:
    """Normalize email; allow localhost/test domains for local development."""
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if "@" not in cleaned:
        raise ValueError("value is not a valid email address")

    local_part, _, domain = cleaned.rpartition("@")
    if not local_part or not domain:
        raise ValueError("value is not a valid email address")

    if allow_test_domains and (
        domain == "localhost" or domain.endswith(".local") or domain.endswith(".test")
    ):
        return cleaned

    try:
        result = validate_email(
            cleaned,
            check_deliverability=False,
            test_environment=allow_test_domains,
        )
        return result.normalized
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc
