"""SMTP email delivery for Цифровое Сукно."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    return bool(settings.smtp_host.strip())


def send_email(*, to_email: str, subject: str, body: str) -> None:
    if not is_smtp_configured():
        logger.warning("SMTP not configured; skip sending email to %s", to_email)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)


def send_verification_email(to_email: str, verify_url: str, expires_minutes: int) -> None:
    send_email(
        to_email=to_email,
        subject="Подтверждение email — Цифровое Сукно",
        body="\n".join(
            [
                "Добро пожаловать в Цифровое Сукно!",
                "",
                "Подтвердите адрес email по ссылке:",
                verify_url,
                "",
                f"Ссылка действует {expires_minutes // 60} ч.",
                "",
                "Если вы не регистрировались — проигнорируйте это письмо.",
            ]
        ),
    )


def send_password_reset_email(to_email: str, reset_url: str, expires_minutes: int) -> None:
    send_email(
        to_email=to_email,
        subject="Сброс пароля — Цифровое Сукно",
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
