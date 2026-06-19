"""Site content and health checks."""

from sqlalchemy import text
from sqlmodel import Session

from app.schemas.site import AboutResponse, SiteStatusResponse
from app.services.contact_service import _to_read, list_contacts
from app.services.email_service import is_smtp_configured
from app.services.site_settings_service import (
    get_site_settings_row,
    settings_skills_list,
)


def get_about(session: Session | None = None) -> AboutResponse:
    """Публичные данные для about / SEO."""
    if session is None:
        from app.core.config import settings

        return AboutResponse(
            owner_name=settings.site_owner_name,
            tagline=settings.site_tagline,
            bio=settings.site_bio,
            experience=settings.site_experience.strip(),
            skills=[s.strip() for s in settings.site_skills.split(",") if s.strip()],
            resume_url=settings.site_resume_url,
            resume_available=bool(settings.site_resume_url),
            motd=settings.site_motd,
            contacts=[],
        )

    row = get_site_settings_row(session)
    contacts = [_to_read(item) for item in list_contacts(session)]
    github_url = ""
    telegram = ""
    resume_url = row.resume_url
    for item in contacts:
        if item.key == "github" and item.href:
            github_url = item.href
        elif item.key == "telegram" and item.href:
            telegram = item.href
        elif item.key == "resume" and item.href:
            resume_url = item.href

    return AboutResponse(
        owner_name=row.owner_name,
        tagline=row.tagline,
        bio=row.bio,
        experience=row.experience.strip(),
        skills=settings_skills_list(session),
        github_url=github_url,
        telegram=telegram,
        resume_url=resume_url,
        resume_available=bool(resume_url),
        motd=row.motd,
        contacts=contacts,
    )


def format_about_terminal(session: Session | None = None) -> str:
    """Текст команды about для терминала."""
    about = get_about(session)
    lines = [
        f"# {about.owner_name}",
        about.tagline,
        "",
        about.bio,
    ]
    if about.skills:
        lines.extend(["", f"Стек: {', '.join(about.skills)}"])
    if about.experience:
        lines.extend(["", "Опыт:"])
        for line in about.experience.replace("\\n", "\n").splitlines():
            stripped = line.strip()
            if stripped:
                lines.append(f"  {stripped}")
    if about.contacts:
        lines.extend(["", "Контакты:"])
        for item in about.contacts:
            if item.href:
                lines.append(f"  {item.label}: {item.value} ({item.href})")
            else:
                lines.append(f"  {item.label}: {item.value}")
    else:
        links: list[str] = []
        if about.github_url:
            links.append(f"GitHub: {about.github_url}")
        if about.telegram:
            links.append(f"Telegram: {about.telegram}")
        if about.resume_url:
            links.append(f"Resume: {about.resume_url}")
        if links:
            lines.extend(["", *links])
    lines.extend(
        ["", "Веб: /about", "Резюме: /resume", "Контакты: contact или /contact", "Портфолио: projects"]
    )
    return "\n".join(lines)


def get_system_status(session: Session | None) -> SiteStatusResponse:
    """Проверить доступность основных компонентов."""
    db_status = "unknown"
    if session is not None:
        try:
            session.exec(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "error"
    smtp_status = "ok" if is_smtp_configured() else "disabled"
    return SiteStatusResponse(
        api="ok",
        database=db_status,
        smtp=smtp_status,
    )


def format_status_terminal(status: SiteStatusResponse) -> str:
    """Текст команды status."""
    return "\n".join(
        [
            "system status:",
            f"  api:      {status.api}",
            f"  database: {status.database}",
            f"  smtp:     {status.smtp}",
            f"  version:  {status.version}",
        ]
    )
