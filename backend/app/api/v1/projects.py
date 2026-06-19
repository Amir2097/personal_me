"""Portfolio project endpoints."""

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.api.deps import get_current_admin_user, get_optional_access_token
from app.core.db import get_session
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, parse_gallery_urls
from app.services.project_service import (
    create_project,
    delete_project,
    get_project_by_id,
    get_visible_project,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_read(item) -> ProjectRead:
    return ProjectRead(
        id=item.id,
        slug=item.slug,
        title=item.title,
        summary=item.summary,
        description=item.description,
        tech_stack=item.tech_stack,
        github_url=item.github_url,
        demo_url=item.demo_url,
        image_url=item.image_url,
        gallery=parse_gallery_urls(item.gallery_urls),
        is_public=item.is_public,
        featured=item.featured,
        sort_order=item.sort_order,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _include_private(token: str | None) -> bool:
    """Авторизованные пользователи видят приватные проекты."""
    if not token:
        return False
    try:
        from app.api.deps import get_current_username_from_token

        get_current_username_from_token(token)
        return True
    except Exception:
        return False


@router.get(
    "",
    response_model=list[ProjectRead],
    summary="Публичные проекты",
    description="Список проектов портфолио. Гостям — только public.",
)
def get_projects(
    session: Session = Depends(get_session),
    token: str | None = Depends(get_optional_access_token),
    featured: bool = False,
) -> list[ProjectRead]:
    """Вернуть проекты с учётом видимости."""
    items = list_projects(
        session,
        include_private=_include_private(token),
        featured_only=featured,
    )
    return [_to_read(item) for item in items]


@router.get(
    "/all",
    response_model=list[ProjectRead],
    summary="Все проекты (admin)",
)
def get_all_projects(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[ProjectRead]:
    """Полный список для админки."""
    return [_to_read(item) for item in list_projects(session, include_private=True)]


@router.get(
    "/{slug}",
    response_model=ProjectRead,
    summary="Проект по slug",
)
def get_project(
    slug: str,
    session: Session = Depends(get_session),
    token: str | None = Depends(get_optional_access_token),
) -> ProjectRead:
    """Вернуть один проект."""
    item = get_visible_project(session, slug, include_private=_include_private(token))
    return _to_read(item)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=201,
    summary="Создать проект (admin)",
)
def post_project(
    payload: ProjectCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> ProjectRead:
    """Создать проект."""
    return _to_read(create_project(session, payload))


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Обновить проект (admin)",
)
def patch_project(
    project_id: int,
    payload: ProjectUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> ProjectRead:
    """Обновить проект."""
    return _to_read(update_project(session, project_id, payload))


@router.delete(
    "/{project_id}",
    status_code=204,
    summary="Удалить проект (admin)",
)
def remove_project(
    project_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Response:
    """Удалить проект."""
    delete_project(session, project_id)
    return Response(status_code=204)
