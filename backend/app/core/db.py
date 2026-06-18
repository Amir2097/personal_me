"""Database setup."""

from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings
from app.models.integration import Integration  # noqa: F401
from app.models.oauth_authorization_code import OAuthAuthorizationCode  # noqa: F401
from app.models.oauth_client import OAuthClient  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.sso_code import SsoCode  # noqa: F401
from app.models.user import User  # noqa: F401

engine = create_engine(settings.postgres_dsn, echo=False)


def create_db_and_tables() -> None:
    """Create all SQLModel tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield SQLModel session for request scope."""
    with Session(engine) as session:
        yield session
