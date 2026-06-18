"""SMTP email delivery."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Return True when SMTP host is set."""
    return bool(settings.smtp_host.strip())


def send_password_reset_email(to_email: str, reset_url: str, expires_minutes: int) -> None:
    """Send password reset link to the user."""
    if not is_smtp_configured():
        logger.warning("SMTP not configured; skip sending reset email to %s", to_email)
        return

    message = EmailMessage()
    message["Subject"] = "Сброс пароля — Personal Me"
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(
        "\n".join(
            [
                "Вы запросили сброс пароля.",
                "",
                f"Перейдите по ссылке (действует {expires_minutes} мин.):",
                reset_url,
                "",
                "Если вы не запрашивали сброс — проигнорируйте это письмо.",
            ]
        )
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
        raise
