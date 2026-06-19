"""Contact channel endpoints."""

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.api.deps import get_current_admin_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from app.services.contact_service import (
    _to_read,
    create_contact,
    delete_contact,
    get_contact_by_id,
    list_contacts,
    update_contact,
)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactRead])
def get_contacts(session: Session = Depends(get_session)) -> list[ContactRead]:
    """Публичный список включённых контактов."""
    return [_to_read(item) for item in list_contacts(session)]


@router.get("/all", response_model=list[ContactRead])
def get_all_contacts(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[ContactRead]:
    """Полный список контактов (admin)."""
    return [_to_read(item) for item in list_contacts(session, include_disabled=True)]


@router.post("", response_model=ContactRead, status_code=201)
def post_contact(
    payload: ContactCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> ContactRead:
    """Создать контакт (admin)."""
    return _to_read(create_contact(session, payload))


@router.patch("/{contact_id}", response_model=ContactRead)
def patch_contact(
    contact_id: int,
    payload: ContactUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> ContactRead:
    """Обновить контакт (admin)."""
    return _to_read(update_contact(session, contact_id, payload))


@router.delete("/{contact_id}", status_code=204)
def remove_contact(
    contact_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Response:
    """Удалить контакт (admin)."""
    delete_contact(session, contact_id)
    return Response(status_code=204)
