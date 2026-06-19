"""CRUD для публичных контактов."""

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.config import settings
from app.models.contact_channel import ContactChannel
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace(" ", "-")


def resolve_contact_href(channel: ContactChannel) -> str | None:
    """Получить кликабельную ссылку для канала."""
    value = channel.value.strip()
    if not value:
        return None
    if channel.kind == "link":
        return value if "://" in value else f"https://{value}"
    if channel.kind == "email":
        return f"mailto:{value}"
    return None


def _to_read(item: ContactChannel) -> ContactRead:
    return ContactRead(
        id=item.id,
        key=item.key,
        label=item.label or item.key,
        value=item.value,
        kind=item.kind,  # type: ignore[arg-type]
        enabled=item.enabled,
        sort_order=item.sort_order,
        href=resolve_contact_href(item),
        created_at=item.created_at,
    )


def ensure_default_contacts(session: Session) -> None:
    """Создать каналы из env при первом запуске."""
    existing_keys = {
        item.key for item in session.exec(select(ContactChannel)).all()
    }
    defaults: list[tuple[str, str, str, str]] = []
    if settings.site_github_url:
        defaults.append(("github", "GitHub", settings.site_github_url, "link"))
    if settings.site_telegram:
        defaults.append(("telegram", "Telegram", settings.site_telegram, "link"))
    if settings.site_resume_url:
        defaults.append(("resume", "Resume", settings.site_resume_url, "link"))
    if settings.initial_admin_email:
        defaults.append(("email", "Email", settings.initial_admin_email, "email"))

    created = False
    for index, (key, label, value, kind) in enumerate(defaults):
        normalized = _normalize_key(key)
        if normalized in existing_keys:
            continue
        session.add(
            ContactChannel(
                key=normalized,
                label=label,
                value=value,
                kind=kind,
                enabled=True,
                sort_order=index,
            )
        )
        created = True
    if created:
        session.commit()


def list_contacts(session: Session, *, include_disabled: bool = False) -> list[ContactChannel]:
    statement = select(ContactChannel).order_by(
        ContactChannel.sort_order, ContactChannel.key
    )
    if not include_disabled:
        statement = statement.where(ContactChannel.enabled == True)  # noqa: E712
    return list(session.exec(statement).all())


def get_contact_by_key(session: Session, key: str) -> ContactChannel | None:
    normalized = _normalize_key(key)
    return session.exec(
        select(ContactChannel).where(ContactChannel.key == normalized)
    ).first()


def get_contact_by_id(session: Session, contact_id: int) -> ContactChannel:
    item = session.get(ContactChannel, contact_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контакт не найден.",
        )
    return item


def create_contact(session: Session, payload: ContactCreate) -> ContactChannel:
    key = _normalize_key(payload.key)
    if get_contact_by_key(session, key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Контакт с таким key уже существует.",
        )
    item = ContactChannel(
        key=key,
        label=payload.label.strip() or key,
        value=payload.value.strip(),
        kind=payload.kind,
        enabled=payload.enabled,
        sort_order=payload.sort_order,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update_contact(
    session: Session, contact_id: int, payload: ContactUpdate
) -> ContactChannel:
    item = get_contact_by_id(session, contact_id)
    if payload.label is not None:
        item.label = payload.label.strip() or item.key
    if payload.value is not None:
        item.value = payload.value.strip()
    if payload.kind is not None:
        item.kind = payload.kind
    if payload.enabled is not None:
        item.enabled = payload.enabled
    if payload.sort_order is not None:
        item.sort_order = payload.sort_order
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_contact(session: Session, contact_id: int) -> None:
    item = get_contact_by_id(session, contact_id)
    session.delete(item)
    session.commit()


def format_contacts_terminal(session: Session) -> str:
    """Текст команды contact."""
    channels = list_contacts(session)
    owner = settings.site_owner_name or "разработчиком"
    if not channels:
        return (
            "Контакты пока не настроены.\n"
            "Admin: /admin/contacts\n"
            "Веб: /contact"
        )
    lines = [f"Связаться с {owner}:", ""]
    for item in channels:
        href = resolve_contact_href(item)
        label = item.label or item.key
        if href:
            lines.append(f"  {item.key:<12} {label}: {item.value}")
            lines.append(f"               → {href}")
        else:
            lines.append(f"  {item.key:<12} {label}: {item.value}")
    lines.extend(
        [
            "",
            "Открыть канал: contact <key>  (например contact telegram)",
            "Веб: /contact",
        ]
    )
    return "\n".join(lines)
