"""Public SEO + admin site settings for Цифровое Сукно."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_admin, unlock_admin_session
from app.core.config import settings
from app.core.db import get_session
from app.schemas.auth import AdminUserSummary, AdminUserUpdate, UserProfile
from app.schemas.site import (
    AdminUnlockRequest,
    AdminUnlockResponse,
    AuditLogEntry,
    SiteSeoPublic,
    SiteSettingsRead,
    SiteSettingsUpdate,
)
from app.services import audit_service, auth_service, site_settings_service

router = APIRouter(prefix="/site", tags=["site"])


def _admin_actor(admin_username: str) -> str:
    return admin_username if admin_username != "sukno_admin" else settings.initial_admin_username


@router.get("/seo", response_model=SiteSeoPublic, summary="Публичные SEO-данные")
def read_public_seo(session: Session = Depends(get_session)) -> SiteSeoPublic:
    return site_settings_service.get_public_seo(session)


@router.post("/admin/unlock", response_model=AdminUnlockResponse, summary="Legacy: открыть админ-сессию ключом")
def unlock_admin(payload: AdminUnlockRequest, session: Session = Depends(get_session)) -> AdminUnlockResponse:
    token = unlock_admin_session(payload.key)
    audit_service.record_legacy_unlock(session)
    return AdminUnlockResponse(access_token=token)


@router.get("/settings", response_model=SiteSettingsRead, summary="Настройки сайта (admin)")
def read_site_settings(
    session: Session = Depends(get_session),
    _: str = Depends(get_current_admin),
) -> SiteSettingsRead:
    return site_settings_service.get_site_settings(session)


@router.patch("/settings", response_model=SiteSettingsRead, summary="Обновить SEO и тексты (admin)")
def patch_site_settings(
    payload: SiteSettingsUpdate,
    session: Session = Depends(get_session),
    admin_username: str = Depends(get_current_admin),
) -> SiteSettingsRead:
    return site_settings_service.update_site_settings(
        session,
        payload,
        actor_username=_admin_actor(admin_username),
    )


@router.get("/admin/audit", response_model=list[AuditLogEntry], summary="Журнал админ-действий")
def read_audit_log(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    _: str = Depends(get_current_admin),
) -> list[AuditLogEntry]:
    rows = audit_service.list_recent(session, limit=limit)
    return [AuditLogEntry(**audit_service.entry_to_dict(row)) for row in rows]


@router.get("/admin/users", response_model=list[AdminUserSummary], summary="Список пользователей (admin)")
def list_users(
    session: Session = Depends(get_session),
    admin_username: str = Depends(get_current_admin),
) -> list[AdminUserSummary]:
    profiles = auth_service.list_users(session)
    return [
        AdminUserSummary(
            username=item.username,
            email=item.email,
            role=item.role,
            display_name=item.display_name,
            email_verified=item.email_verified,
            is_active=item.is_active,
            created_at=item.created_at,  # type: ignore[arg-type]
            last_login_at=item.last_login_at,
        )
        for item in profiles
    ]


@router.patch("/admin/users/{username}", response_model=UserProfile, summary="Обновить пользователя (admin)")
def patch_user(
    username: str,
    payload: AdminUserUpdate,
    session: Session = Depends(get_session),
    admin_username: str = Depends(get_current_admin),
) -> UserProfile:
    return auth_service.admin_update_user(
        session,
        username,
        role=payload.role,
        is_active=payload.is_active,
        display_name=payload.display_name,
        actor_username=_admin_actor(admin_username),
    )
