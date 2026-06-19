"""Project API schemas."""

import re
from datetime import datetime

from pydantic import BaseModel, Field


def parse_gallery_urls(raw: str) -> list[str]:
    """Разобрать список URL из строки (по строкам или запятым)."""
    urls: list[str] = []
    for part in re.split(r"[\n,]+", raw):
        value = part.strip()
        if value:
            urls.append(value)
    return urls


class ProjectCreate(BaseModel):
    """Создание проекта."""

    slug: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=128)
    summary: str = ""
    description: str = ""
    tech_stack: str = ""
    github_url: str = ""
    demo_url: str = ""
    image_url: str = ""
    gallery_urls: str = ""
    is_public: bool = True
    featured: bool = False
    sort_order: int = 0


class ProjectUpdate(BaseModel):
    """Частичное обновление проекта."""

    title: str | None = None
    summary: str | None = None
    description: str | None = None
    tech_stack: str | None = None
    github_url: str | None = None
    demo_url: str | None = None
    image_url: str | None = None
    gallery_urls: str | None = None
    is_public: bool | None = None
    featured: bool | None = None
    sort_order: int | None = None


class ProjectRead(BaseModel):
    """Проект в ответе API."""

    id: int
    slug: str
    title: str
    summary: str
    description: str
    tech_stack: str
    github_url: str
    demo_url: str
    image_url: str
    gallery: list[str]
    is_public: bool
    featured: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
