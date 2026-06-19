"""Feedback form handling."""

from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.feedback import FeedbackCreate
from app.services.email_service import is_smtp_configured, send_feedback_email


def feedback_recipient() -> str:
    """Email получателя обратной связи."""
    explicit = settings.feedback_to_email.strip()
    if explicit:
        return explicit
    return settings.initial_admin_email.strip()


def is_feedback_enabled() -> bool:
    """Форма доступна, если настроены SMTP и адрес получателя."""
    return is_smtp_configured() and bool(feedback_recipient())


def submit_feedback(payload: FeedbackCreate) -> None:
    """Отправить сообщение на email оператора."""
    if payload.company.strip():
        return

    if not is_feedback_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Форма обратной связи временно недоступна.",
        )

    send_feedback_email(
        to_email=feedback_recipient(),
        sender_name=payload.name.strip(),
        sender_email=str(payload.email),
        message=payload.message.strip(),
    )
