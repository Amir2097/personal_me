"""SEO and site-settings DTOs for Цифровое Сукно."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

BRAND_NAME = "Цифровое Сукно"


class SiteSeoPublic(BaseModel):
    brand_name: str = BRAND_NAME
    tagline: str
    site_url: str
    seo_title: str
    seo_description: str
    seo_keywords: str
    og_image_url: str
    motd: str


class SiteSettingsRead(SiteSeoPublic):
    updated_at: datetime


class SiteSettingsUpdate(BaseModel):
    tagline: str | None = Field(default=None, max_length=240)
    site_url: str | None = Field(default=None, max_length=500)
    seo_title: str | None = Field(default=None, max_length=160)
    seo_description: str | None = Field(default=None, max_length=600)
    seo_keywords: str | None = Field(default=None, max_length=400)
    og_image_url: str | None = Field(default=None, max_length=500)
    motd: str | None = Field(default=None, max_length=280)


class AdminUnlockRequest(BaseModel):
    key: str = Field(min_length=1, max_length=200)


class AdminUnlockResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "admin"


class AuditLogEntry(BaseModel):
    id: int
    created_at: datetime
    actor_username: str
    action: str
    target: str
    details: dict[str, Any] = Field(default_factory=dict)
