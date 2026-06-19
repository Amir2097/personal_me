"""SMTP email delivery."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Return True when SMTP host is set."""
    return bool(settings.smtp_host.strip())


def send_email(*, to_email: str, subject: str, body: str, reply_to: str | None = None) -> None:
    """Send a plain-text email."""
    if not is_smtp_configured():
        logger.warning("SMTP not configured; skip sending email to %s", to_email)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to_email
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        raise


def send_password_reset_email(to_email: str, reset_url: str, expires_minutes: int) -> None:
    """Send password reset link to the user."""
    send_email(
        to_email=to_email,
        subject="Сброс пароля — Personal Me",
        body="\n".join(
            [
                "Вы запросили сброс пароля.",
                "",
                f"Перейдите по ссылке (действует {expires_minutes} мин.):",
                reset_url,
                "",
                "Если вы не запрашивали сброс — проигнорируйте это письмо.",
            ]
        ),
    )


def send_feedback_email(
    *,
    to_email: str,
    sender_name: str,
    sender_email: str,
    message: str,
) -> None:
    """Notify site owner about a feedback form submission."""
    send_email(
        to_email=to_email,
        subject=f"Обратная связь — {sender_name}",
        reply_to=sender_email,
        body="\n".join(
            [
                "Новое сообщение с формы обратной связи:",
                "",
                f"Имя: {sender_name}",
                f"Email: {sender_email}",
                "",
                message,
            ]
        ),
    )
