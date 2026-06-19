"""Public feedback form endpoints."""

from fastapi import APIRouter, Request

from app.core.rate_limit import check_feedback_rate_limit
from app.schemas.feedback import FeedbackConfigResponse, FeedbackCreate, FeedbackResponse
from app.services.feedback_service import is_feedback_enabled, submit_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/config", response_model=FeedbackConfigResponse)
def feedback_config() -> FeedbackConfigResponse:
    """Проверить, доступна ли форма обратной связи."""
    return FeedbackConfigResponse(enabled=is_feedback_enabled())


@router.post("", response_model=FeedbackResponse, status_code=201)
def post_feedback(payload: FeedbackCreate, request: Request) -> FeedbackResponse:
    """Отправить сообщение обратной связи."""
    check_feedback_rate_limit(request)
    submit_feedback(payload)
    return FeedbackResponse(message="Сообщение отправлено. Спасибо!")
