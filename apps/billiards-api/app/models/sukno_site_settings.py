"""Singleton site / SEO settings for Цифровое Сукно.

Brand name is fixed in the product. This row stores install SEO, canonical URL
and optional home copy — not a second club identity.
"""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SuknoSiteSettings(SQLModel, table=True):
    __tablename__ = "sukno_site_settings"

    id: int = Field(default=1, primary_key=True)
    tagline: str = Field(default="", max_length=240, nullable=False)
    site_url: str = Field(default="", max_length=500, nullable=False)
    seo_title: str = Field(default="Цифровое Сукно", max_length=160, nullable=False)
    seo_description: str = Field(
        default="Цифровое Сукно — тренажёр, колхоз и турнирная сетка для русского бильярда.",
        max_length=600,
        nullable=False,
    )
    seo_keywords: str = Field(
        default="бильярд, русская пирамида, колхоз, турнир, академия",
        max_length=400,
        nullable=False,
    )
    og_image_url: str = Field(default="", max_length=500, nullable=False)
    motd: str = Field(default="", max_length=280, nullable=False)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
