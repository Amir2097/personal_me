"""Singleton site / SEO settings."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SiteSettings(SQLModel, table=True):
    """Единственная строка настроек сайта и SEO (id=1)."""

    id: int = Field(default=1, primary_key=True)
    site_name: str = Field(default="personal_me", nullable=False)
    owner_name: str = Field(default="", nullable=False)
    tagline: str = Field(default="", nullable=False)
    bio: str = Field(default="", nullable=False)
    experience: str = Field(default="", nullable=False)
    skills: str = Field(default="", nullable=False)
    site_url: str = Field(default="http://localhost", nullable=False)
    seo_title_suffix: str = Field(default="Terminal IDE", nullable=False)
    seo_description: str = Field(default="", nullable=False)
    seo_keywords: str = Field(default="", nullable=False)
    og_image_url: str = Field(default="", nullable=False)
    motd: str = Field(default="", nullable=False)
    resume_url: str = Field(default="", nullable=False)
    privacy_policy: str = Field(default="", nullable=False)
    terms_of_use: str = Field(default="", nullable=False)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
