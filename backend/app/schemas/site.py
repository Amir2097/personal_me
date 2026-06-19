"""Public site content and health DTOs."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.contact import ContactRead


class SiteSeoPublic(BaseModel):
    """Публичные SEO-данные для meta-тегов."""

    site_name: str
    owner_name: str
    tagline: str
    site_url: str
    seo_title_suffix: str
    seo_description: str
    seo_keywords: str
    og_image_url: str



class SiteSettingsRead(BaseModel):
    """Полные настройки сайта (admin)."""

    site_name: str
    owner_name: str
    tagline: str
    bio: str
    experience: str
    skills: str
    site_url: str
    seo_title_suffix: str
    seo_description: str
    seo_keywords: str
    og_image_url: str
    motd: str
    resume_url: str
    privacy_policy: str
    terms_of_use: str
    updated_at: datetime


class SiteSettingsUpdate(BaseModel):
    """Частичное обновление настроек (admin)."""

    site_name: str | None = None
    owner_name: str | None = None
    tagline: str | None = None
    bio: str | None = None
    experience: str | None = None
    skills: str | None = None
    site_url: str | None = None
    seo_title_suffix: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    motd: str | None = None
    resume_url: str | None = None
    privacy_policy: str | None = None
    terms_of_use: str | None = None


class SiteLegalPublic(BaseModel):
    """Публичные юридические тексты."""

    site_name: str
    owner_name: str
    site_url: str
    privacy_policy: str
    terms_of_use: str
    updated_at: datetime


class AboutResponse(BaseModel):
    """Публичная информация «обо мне»."""

    owner_name: str
    tagline: str
    bio: str
    experience: str = ""
    skills: list[str]
    github_url: str = ""
    telegram: str = ""
    resume_url: str = ""
    resume_available: bool = False
    resume_path: str = "/resume"
    motd: str = ""
    web_path: str = "/about"
    contacts: list[ContactRead] = Field(default_factory=list)


class SiteStatusResponse(BaseModel):
    """Статус компонентов системы."""

    api: str = "ok"
    database: str = "unknown"
    smtp: str = "disabled"
    version: str = "0.1.0"


class ProfileUpdateRequest(BaseModel):
    """Обновление профиля пользователя."""

    email: str | None = None
