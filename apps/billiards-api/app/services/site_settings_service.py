"""Install SEO for Цифровое Сукно. Brand name is not stored here."""

from datetime import datetime, timezone

from sqlmodel import Session

from app.models.sukno_site_settings import SuknoSiteSettings
from app.schemas.site import BRAND_NAME, SiteSeoPublic, SiteSettingsRead, SiteSettingsUpdate

_DEFAULT_DESCRIPTION = (
    "Цифровое Сукно — тренажёр, колхоз и турнирная сетка для русского бильярда."
)
_DEFAULT_KEYWORDS = "бильярд, русская пирамида, колхоз, турнир, академия"


def ensure_default_site_settings(session: Session) -> SuknoSiteSettings:
    row = session.get(SuknoSiteSettings, 1)
    if row:
        return row
    row = SuknoSiteSettings(
        id=1,
        seo_title=BRAND_NAME,
        seo_description=_DEFAULT_DESCRIPTION,
        seo_keywords=_DEFAULT_KEYWORDS,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _to_read(row: SuknoSiteSettings) -> SiteSettingsRead:
    return SiteSettingsRead(
        brand_name=BRAND_NAME,
        tagline=row.tagline,
        site_url=row.site_url.rstrip("/"),
        seo_title=row.seo_title.strip() or BRAND_NAME,
        seo_description=row.seo_description.strip() or _DEFAULT_DESCRIPTION,
        seo_keywords=row.seo_keywords,
        og_image_url=row.og_image_url.strip(),
        motd=row.motd,
        updated_at=row.updated_at,
    )


def get_site_settings(session: Session) -> SiteSettingsRead:
    return _to_read(ensure_default_site_settings(session))


def get_public_seo(session: Session) -> SiteSeoPublic:
    full = get_site_settings(session)
    return SiteSeoPublic(
        brand_name=full.brand_name,
        tagline=full.tagline,
        site_url=full.site_url,
        seo_title=full.seo_title,
        seo_description=full.seo_description,
        seo_keywords=full.seo_keywords,
        og_image_url=full.og_image_url,
        motd=full.motd,
    )


def update_site_settings(
    session: Session,
    payload: SiteSettingsUpdate,
    *,
    actor_username: str | None = None,
) -> SiteSettingsRead:
    row = ensure_default_site_settings(session)
    changes: dict[str, dict[str, str]] = {}
    for field in (
        "tagline",
        "site_url",
        "seo_title",
        "seo_description",
        "seo_keywords",
        "og_image_url",
        "motd",
    ):
        value = getattr(payload, field)
        if value is not None:
            new_value = value.strip() if isinstance(value, str) else value
            old_value = getattr(row, field)
            if isinstance(old_value, str):
                old_value = old_value.strip()
            if new_value != old_value:
                changes[field] = {"from": old_value, "to": new_value}
            setattr(row, field, new_value)
    if not row.seo_title.strip():
        row.seo_title = BRAND_NAME
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)

    if actor_username and changes:
        from app.services import audit_service

        audit_service.record_site_settings_update(
            session,
            actor_username=actor_username,
            changes=changes,
        )
    return _to_read(row)
