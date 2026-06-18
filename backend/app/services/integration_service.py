"""CRUD и загрузка внешних интеграций."""

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.integration import Integration
from app.schemas.integration import IntegrationCreate, IntegrationUpdate
from app.services.integrations_config import (
    DEFAULT_INTEGRATIONS,
    ExternalService,
    merge_env_overrides,
)


def _normalize_key(key: str) -> str:
    return key.strip().lower()


def ensure_default_integrations(session: Session) -> None:
    """Заполнить таблицу дефолтными сервисами при первом запуске."""
    existing_keys = {
        item.key for item in session.exec(select(Integration)).all()
    }
    created = False
    for index, (key, data) in enumerate(DEFAULT_INTEGRATIONS.items()):
        normalized = _normalize_key(key)
        if normalized in existing_keys:
            continue
        session.add(
            Integration(
                key=normalized,
                url=str(data["url"]),
                label=str(data.get("label", key)),
                requires_auth=bool(data.get("requires_auth", False)),
                use_sso=bool(data.get("use_sso", False)),
                enabled=True,
                sort_order=index,
            )
        )
        created = True
    if created:
        session.commit()


def load_integrations(session: Session) -> dict[str, ExternalService]:
    """Загрузить включённые интеграции из БД с overlay из env."""
    rows = session.exec(
        select(Integration)
        .where(Integration.enabled == True)  # noqa: E712
        .order_by(Integration.sort_order, Integration.key)
    ).all()
    result = {
        row.key: ExternalService(
            url=row.url,
            requires_auth=row.requires_auth,
            label=row.label or row.key,
            use_sso=row.use_sso,
        )
        for row in rows
    }
    return merge_env_overrides(result)


def list_integrations(session: Session, *, include_disabled: bool = False) -> list[Integration]:
    """Список интеграций для REST API."""
    statement = select(Integration).order_by(Integration.sort_order, Integration.key)
    if not include_disabled:
        statement = statement.where(Integration.enabled == True)  # noqa: E712
    return list(session.exec(statement).all())


def get_integration_by_id(session: Session, integration_id: int) -> Integration:
    """Найти интеграцию по id."""
    item = session.get(Integration, integration_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Интеграция не найдена.",
        )
    return item


def get_integration_by_key(session: Session, key: str) -> Integration:
    """Найти интеграцию по ключу."""
    normalized = _normalize_key(key)
    item = session.exec(select(Integration).where(Integration.key == normalized)).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Интеграция не найдена.",
        )
    return item


def create_integration(session: Session, payload: IntegrationCreate) -> Integration:
    """Создать интеграцию."""
    normalized = _normalize_key(payload.key)
    existing = session.exec(select(Integration).where(Integration.key == normalized)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Интеграция с таким ключом уже существует.",
        )
    item = Integration(
        key=normalized,
        url=payload.url.strip(),
        label=payload.label.strip() or normalized,
        requires_auth=payload.requires_auth,
        use_sso=payload.use_sso,
        enabled=payload.enabled,
        sort_order=payload.sort_order,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update_integration(
    session: Session, integration_id: int, payload: IntegrationUpdate
) -> Integration:
    """Обновить интеграцию."""
    item = get_integration_by_id(session, integration_id)
    data = payload.model_dump(exclude_unset=True)
    if "url" in data and data["url"] is not None:
        data["url"] = data["url"].strip()
    if "label" in data and data["label"] is not None:
        data["label"] = data["label"].strip()
    for field, value in data.items():
        setattr(item, field, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_integration(session: Session, integration_id: int) -> None:
    """Удалить интеграцию."""
    item = get_integration_by_id(session, integration_id)
    session.delete(item)
    session.commit()
