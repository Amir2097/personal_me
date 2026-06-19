"""Public site endpoints."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_admin_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.site import (
    AboutResponse,
    SiteLegalPublic,
    SiteSeoPublic,
    SiteSettingsRead,
    SiteSettingsUpdate,
    SiteStatusResponse,
)
from app.services.site_service import get_about, get_system_status
from app.services.site_settings_service import (
    get_public_legal,
    get_public_seo,
    get_site_settings,
    update_site_settings,
)

router = APIRouter(prefix="/site", tags=["site"])


@router.get("/seo", response_model=SiteSeoPublic)
def site_seo(session: Session = Depends(get_session)) -> SiteSeoPublic:
    """Публичные SEO-данные для meta-тегов."""
    return get_public_seo(session)


@router.get("/legal", response_model=SiteLegalPublic)
def site_legal(session: Session = Depends(get_session)) -> SiteLegalPublic:
    """Публичные юридические тексты (политика и соглашение)."""
    return get_public_legal(session)


@router.get("/settings", response_model=SiteSettingsRead)
def site_settings_admin(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> SiteSettingsRead:
    """Настройки сайта и SEO (admin)."""
    return get_site_settings(session)


@router.patch("/settings", response_model=SiteSettingsRead)
def patch_site_settings(
    payload: SiteSettingsUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> SiteSettingsRead:
    """Обновить настройки сайта и SEO (admin)."""
    return update_site_settings(session, payload)


@router.get(
    "/about",
    response_model=AboutResponse,
    summary="Публичная информация about",
)
def site_about(session: Session = Depends(get_session)) -> AboutResponse:
    """Данные для /about и команды about."""
    return get_about(session)


@router.get(
    "/status",
    response_model=SiteStatusResponse,
    summary="Health компонентов",
)
def site_status(session: Session = Depends(get_session)) -> SiteStatusResponse:
    """Статус API, БД и SMTP."""
    return get_system_status(session)
