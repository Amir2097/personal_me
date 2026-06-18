"""Integration management endpoints."""

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.api.deps import get_current_admin_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.integration import IntegrationCreate, IntegrationRead, IntegrationUpdate
from app.services.integration_service import (
    create_integration,
    delete_integration,
    get_integration_by_id,
    list_integrations,
    update_integration,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _to_read(item) -> IntegrationRead:
    return IntegrationRead(
        id=item.id,
        key=item.key,
        url=item.url,
        label=item.label,
        requires_auth=item.requires_auth,
        use_sso=item.use_sso,
        enabled=item.enabled,
        sort_order=item.sort_order,
        created_at=item.created_at,
    )


@router.get(
    "",
    response_model=list[IntegrationRead],
    summary="Список интеграций",
    description="Публичный список включённых внешних сервисов.",
)
def get_integrations(session: Session = Depends(get_session)) -> list[IntegrationRead]:
    """Вернуть включённые интеграции."""
    return [_to_read(item) for item in list_integrations(session)]


@router.get(
    "/all",
    response_model=list[IntegrationRead],
    summary="Все интеграции (admin)",
    description="Полный список интеграций, включая отключённые. Только для администратора.",
)
def get_all_integrations(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[IntegrationRead]:
    """Вернуть все интеграции для админки."""
    return [_to_read(item) for item in list_integrations(session, include_disabled=True)]


@router.get(
    "/{integration_id}",
    response_model=IntegrationRead,
    summary="Интеграция по id",
)
def get_integration(
    integration_id: int,
    session: Session = Depends(get_session),
) -> IntegrationRead:
    """Вернуть одну интеграцию."""
    return _to_read(get_integration_by_id(session, integration_id))


@router.post(
    "",
    response_model=IntegrationRead,
    status_code=201,
    summary="Создать интеграцию (admin)",
)
def post_integration(
    payload: IntegrationCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> IntegrationRead:
    """Создать новую интеграцию."""
    return _to_read(create_integration(session, payload))


@router.patch(
    "/{integration_id}",
    response_model=IntegrationRead,
    summary="Обновить интеграцию (admin)",
)
def patch_integration(
    integration_id: int,
    payload: IntegrationUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> IntegrationRead:
    """Частично обновить интеграцию."""
    return _to_read(update_integration(session, integration_id, payload))


@router.delete(
    "/{integration_id}",
    status_code=204,
    summary="Удалить интеграцию (admin)",
)
def remove_integration(
    integration_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Response:
    """Удалить интеграцию."""
    delete_integration(session, integration_id)
    return Response(status_code=204)
