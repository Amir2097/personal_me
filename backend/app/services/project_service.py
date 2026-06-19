"""CRUD и загрузка проектов портфолио."""

import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, parse_gallery_urls

DEFAULT_PROJECTS: list[dict[str, Any]] = [
    {
        "slug": "personal-me",
        "title": "Personal Me",
        "summary": "Terminal/IDE хаб разработчика с JWT и интеграциями.",
        "description": (
            "Монорепозиторий: FastAPI backend, Nuxt 3 frontend, PostgreSQL, "
            "Docker Compose, терминальный UI и admin-панель."
        ),
        "tech_stack": "Python, FastAPI, Nuxt 3, PostgreSQL, Docker",
        "github_url": "",
        "demo_url": "http://localhost",
        "is_public": True,
        "featured": True,
        "sort_order": 0,
    },
    {
        "slug": "cli-lab",
        "title": "CLI Lab",
        "summary": "Песочница для экспериментов с CLI и автоматизацией.",
        "description": "Набор утилит и скриптов для работы из терминала.",
        "tech_stack": "Python, Bash",
        "github_url": "",
        "demo_url": "",
        "is_public": True,
        "featured": False,
        "sort_order": 1,
    },
    {
        "slug": "infra-playground",
        "title": "Infra Playground",
        "summary": "Черновик: эксперименты с Docker и CI.",
        "description": "Приватный проект для внутренних экспериментов с инфраструктурой.",
        "tech_stack": "Docker, GitHub Actions",
        "github_url": "",
        "demo_url": "",
        "is_public": False,
        "featured": False,
        "sort_order": 2,
    },
]


def _normalize_slug(slug: str) -> str:
    value = slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug может содержать только латиницу, цифры и дефис.",
        )
    return value


def ensure_default_projects(session: Session) -> None:
    """Заполнить таблицу дефолтными проектами при первом запуске."""
    existing_slugs = {item.slug for item in session.exec(select(Project)).all()}
    created = False
    for data in DEFAULT_PROJECTS:
        slug = _normalize_slug(str(data["slug"]))
        if slug in existing_slugs:
            continue
        session.add(
            Project(
                slug=slug,
                title=str(data["title"]),
                summary=str(data.get("summary", "")),
                description=str(data.get("description", "")),
                tech_stack=str(data.get("tech_stack", "")),
                github_url=str(data.get("github_url", "")),
                demo_url=str(data.get("demo_url", "")),
                is_public=bool(data.get("is_public", True)),
                featured=bool(data.get("featured", False)),
                sort_order=int(data.get("sort_order", 0)),
            )
        )
        created = True
    if created:
        session.commit()


def list_projects(
    session: Session,
    *,
    include_private: bool = False,
    featured_only: bool = False,
) -> list[Project]:
    """Список проектов с фильтрами."""
    statement = select(Project).order_by(
        Project.featured.desc(), Project.sort_order, Project.title
    )
    if not include_private:
        statement = statement.where(Project.is_public == True)  # noqa: E712
    if featured_only:
        statement = statement.where(Project.featured == True)  # noqa: E712
    return list(session.exec(statement).all())


def get_project_by_slug(session: Session, slug: str) -> Project:
    """Найти проект по slug."""
    normalized = _normalize_slug(slug)
    item = session.exec(select(Project).where(Project.slug == normalized)).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден.",
        )
    return item


def get_visible_project(session: Session, slug: str, *, include_private: bool) -> Project:
    """Вернуть проект с учётом видимости."""
    item = get_project_by_slug(session, slug)
    if not item.is_public and not include_private:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден.",
        )
    return item


def get_project_by_id(session: Session, project_id: int) -> Project:
    """Найти проект по id."""
    item = session.get(Project, project_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден.",
        )
    return item


def create_project(session: Session, payload: ProjectCreate) -> Project:
    """Создать проект."""
    slug = _normalize_slug(payload.slug)
    existing = session.exec(select(Project).where(Project.slug == slug)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Проект с таким slug уже существует.",
        )
    now = datetime.now(timezone.utc)
    item = Project(
        slug=slug,
        title=payload.title.strip(),
        summary=payload.summary.strip(),
        description=payload.description.strip(),
        tech_stack=payload.tech_stack.strip(),
        github_url=payload.github_url.strip(),
        demo_url=payload.demo_url.strip(),
        image_url=payload.image_url.strip(),
        gallery_urls=payload.gallery_urls.strip(),
        is_public=payload.is_public,
        featured=payload.featured,
        sort_order=payload.sort_order,
        created_at=now,
        updated_at=now,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update_project(session: Session, project_id: int, payload: ProjectUpdate) -> Project:
    """Обновить проект."""
    item = get_project_by_id(session, project_id)
    data = payload.model_dump(exclude_unset=True)
    for field in (
        "title",
        "summary",
        "description",
        "tech_stack",
        "github_url",
        "demo_url",
        "image_url",
        "gallery_urls",
    ):
        if field in data and data[field] is not None:
            data[field] = str(data[field]).strip()
    for field, value in data.items():
        setattr(item, field, value)
    item.updated_at = datetime.now(timezone.utc)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_project(session: Session, project_id: int) -> None:
    """Удалить проект."""
    item = get_project_by_id(session, project_id)
    session.delete(item)
    session.commit()


def format_projects_list(projects: list[Project]) -> str:
    """Текстовый список для terminal-команды."""
    if not projects:
        return "Проекты не найдены. Откройте /projects"
    featured = [item for item in projects if item.featured]
    regular = [item for item in projects if not item.featured]
    lines = ["Проекты:"]
    if featured:
        lines.append("")
        lines.append("★ Featured:")
        for item in featured:
            lines.extend(_project_line(item))
    if regular:
        if featured:
            lines.append("")
            lines.append("Остальные:")
        for item in regular:
            lines.extend(_project_line(item))
    lines.append("")
    lines.append("Подробнее: project <slug>  |  Веб: /projects")
    return "\n".join(lines)


def _project_line(item: Project) -> list[str]:
    visibility = "public" if item.is_public else "private"
    featured = " ★" if item.featured else ""
    lines = [f"  - {item.slug}{featured}: {item.title} ({visibility})"]
    if item.summary:
        lines.append(f"    {item.summary}")
    return lines


def format_project_detail(project: Project) -> str:
    """Текстовая карточка проекта для terminal."""
    lines = [
        f"#{project.title} ({project.slug})",
        project.summary,
    ]
    if project.tech_stack:
        lines.append(f"Стек: {project.tech_stack}")
    if project.description:
        lines.append(project.description)
    if project.github_url:
        lines.append(f"GitHub: {project.github_url}")
    if project.demo_url:
        lines.append(f"Demo: {project.demo_url}")
    lines.append(f"Веб: /projects/{project.slug}")
    return "\n".join(lines)
