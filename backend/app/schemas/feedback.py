"""Feedback form DTOs."""

from pydantic import BaseModel, EmailStr, Field


class FeedbackCreate(BaseModel):
    """Сообщение обратной связи с сайта."""

    name: str = Field(min_length=1, max_length=128)
    email: EmailStr
    message: str = Field(min_length=10, max_length=5000)
    company: str = Field(default="", max_length=200)


class FeedbackConfigResponse(BaseModel):
    """Публичные настройки формы обратной связи."""

    enabled: bool


class FeedbackResponse(BaseModel):
    """Ответ после отправки формы."""

    message: str
