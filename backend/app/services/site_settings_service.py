"""Site settings CRUD and SEO helpers."""

from datetime import datetime, timezone

from sqlmodel import Session

from app.core.config import settings
from app.models.site_settings import SiteSettings
from app.schemas.site import (
    SiteLegalPublic,
    SiteSeoPublic,
    SiteSettingsRead,
    SiteSettingsUpdate,
)
from app.services.legal_templates import default_privacy_policy, default_terms_of_use
from app.services.legal_templates import default_privacy_policy, default_terms_of_use


def _skills_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _defaults_from_env() -> SiteSettings:
    return SiteSettings(
        id=1,
        site_name="personal_me",
        owner_name=settings.site_owner_name,
        tagline=settings.site_tagline,
        bio=settings.site_bio,
        experience=settings.site_experience,
        skills=settings.site_skills,
        site_url=settings.site_url,
        seo_title_suffix="Terminal IDE",
        seo_description=settings.site_tagline,
        seo_keywords=settings.site_skills,
        og_image_url="",
        motd=settings.site_motd,
        resume_url=settings.site_resume_url,
    )


def ensure_default_site_settings(session: Session) -> None:
    """Создать строку настроек из env при первом запуске."""
    existing = session.get(SiteSettings, 1)
    if existing:
        return
    row = _defaults_from_env()
    session.add(row)
    session.commit()


def get_site_settings_row(session: Session) -> SiteSettings:
    ensure_default_site_settings(session)
    row = session.get(SiteSettings, 1)
    assert row is not None
    return row


def _legal_kwargs(row: SiteSettings) -> dict[str, str]:
    return {
        "site_name": row.site_name,
        "owner_name": row.owner_name,
        "site_url": row.site_url.rstrip("/"),
    }


def _resolved_privacy(row: SiteSettings) -> str:
    if row.privacy_policy.strip():
        return row.privacy_policy.strip()
    return default_privacy_policy(**_legal_kwargs(row))


def _resolved_terms(row: SiteSettings) -> str:
    if row.terms_of_use.strip():
        return row.terms_of_use.strip()
    return default_terms_of_use(**_legal_kwargs(row))


def _to_read(row: SiteSettings) -> SiteSettingsRead:
    return SiteSettingsRead(
        site_name=row.site_name,
        owner_name=row.owner_name,
        tagline=row.tagline,
        bio=row.bio,
        experience=row.experience,
        skills=row.skills,
        site_url=row.site_url,
        seo_title_suffix=row.seo_title_suffix,
        seo_description=row.seo_description,
        seo_keywords=row.seo_keywords,
        og_image_url=row.og_image_url,
        motd=row.motd,
        resume_url=row.resume_url,
        privacy_policy=row.privacy_policy,
        terms_of_use=row.terms_of_use,
        updated_at=row.updated_at,
    )


def get_site_settings(session: Session) -> SiteSettingsRead:
    return _to_read(get_site_settings_row(session))


def get_public_seo(session: Session) -> SiteSeoPublic:
    row = get_site_settings_row(session)
    description = row.seo_description.strip() or row.tagline
    return SiteSeoPublic(
        site_name=row.site_name,
        owner_name=row.owner_name,
        tagline=row.tagline,
        site_url=row.site_url.rstrip("/"),
        seo_title_suffix=row.seo_title_suffix,
        seo_description=description,
        seo_keywords=row.seo_keywords,
        og_image_url=row.og_image_url,
    )


def get_public_legal(session: Session) -> SiteLegalPublic:
    row = get_site_settings_row(session)
    return SiteLegalPublic(
        site_name=row.site_name,
        owner_name=row.owner_name,
        site_url=row.site_url.rstrip("/"),
        privacy_policy=_resolved_privacy(row),
        terms_of_use=_resolved_terms(row),
        updated_at=row.updated_at,
    )


def update_site_settings(session: Session, payload: SiteSettingsUpdate) -> SiteSettingsRead:
    row = get_site_settings_row(session)
    for field in (
        "site_name",
        "owner_name",
        "tagline",
        "bio",
        "experience",
        "skills",
        "site_url",
        "seo_title_suffix",
        "seo_description",
        "seo_keywords",
        "og_image_url",
        "motd",
        "resume_url",
        "privacy_policy",
        "terms_of_use",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(row, field, value.strip() if isinstance(value, str) else value)
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_read(row)


def settings_skills_list(session: Session) -> list[str]:
    return _skills_list(get_site_settings_row(session).skills)
