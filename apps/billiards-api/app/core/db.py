"""Database setup for Цифровое Сукно."""

from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings
from app.models.academy_progress import AcademyProgress  # noqa: F401
from app.models.cup_session import CupSession  # noqa: F401
from app.models.cup_tournament import CupTournament  # noqa: F401
from app.models.kolkhoz_game import KolkhozGame  # noqa: F401
from app.models.kolkhoz_session import KolkhozSession  # noqa: F401
from app.models.sukno_email_verification_token import SuknoEmailVerificationToken  # noqa: F401
from app.models.sukno_audit_log import SuknoAuditLog  # noqa: F401
from app.models.sukno_password_reset_token import SuknoPasswordResetToken  # noqa: F401
from app.models.sukno_refresh_token import SuknoRefreshToken  # noqa: F401
from app.models.sukno_site_settings import SuknoSiteSettings  # noqa: F401
from app.models.sukno_user import SuknoUser  # noqa: F401

engine = create_engine(settings.postgres_dsn, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_profile_columns()


def _ensure_profile_columns() -> None:
    """Add profile columns on existing databases (create_all does not ALTER)."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "sukno_user" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("sukno_user")}
    additions = {
        "avatar_url": "ALTER TABLE sukno_user ADD COLUMN avatar_url VARCHAR NOT NULL DEFAULT ''",
        "bio": "ALTER TABLE sukno_user ADD COLUMN bio VARCHAR NOT NULL DEFAULT ''",
        "location": "ALTER TABLE sukno_user ADD COLUMN location VARCHAR NOT NULL DEFAULT ''",
        "telegram": "ALTER TABLE sukno_user ADD COLUMN telegram VARCHAR NOT NULL DEFAULT ''",
    }
    missing = [sql for name, sql in additions.items() if name not in existing]
    if not missing:
        return
    with engine.begin() as conn:
        for stmt in missing:
            conn.execute(text(stmt))


def get_session():
    with Session(engine) as session:
        yield session
