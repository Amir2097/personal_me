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


def get_session():
    with Session(engine) as session:
        yield session
